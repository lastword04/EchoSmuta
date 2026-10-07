import { useState } from 'react';
import { useDispatch } from 'react-redux';
import { Card } from '../../../../shared/ui/Card/Card';
import { Button } from '../../../../shared/ui/Button/Button';
import { Input } from '../../../../shared/ui/Input/Input';
import { Select } from '../../../../shared/ui/Select/Select';
import { 
  useGetExchangeSettingsQuery,
  useGetLotsQuery,
  useCreateLotMutation,
  useBuyLotMutation,
  useDeleteLotMutation,
} from '../../api/currencyApi';
import { characterApi } from '../../api/characterApi';
import { useAutoFontSize } from '../../../../shared/hooks/ui/useAutoFontSize';
import styles from './CurrencyExchangeForm.module.css';
import { intInputHandler, decimalInputHandler } from '../../../../shared/lib/validation/numberInput';


const CharacterName = ({ name }) => {
  const nameRef = useAutoFontSize(window.innerWidth - 180, 18, 5, 0);
  
  return (
    <span ref={nameRef} className={styles.characterName}>
      {name}
    </span>
  );
};

export const CurrencyExchangeForm = ({ onSuccess, onCancel, characters }) => {
  const dispatch = useDispatch();

  // Состояние вкладок и пагинации
  const [activeTab, setActiveTab] = useState('gold');
  const [currentPage, setCurrentPage] = useState(1);

  // Хуки API — мгновенный рендер с дефолтными значениями
  const { data: exchangeSettings = {} } = useGetExchangeSettingsQuery();
  const { 
    data: lotsData = { objects: [], count: 0 },   
    isFetching: lotsFetching,
  } = useGetLotsQuery({ 
    buyFor: activeTab, 
    limit: 10, 
    offset: (currentPage - 1) * 10 
  });
  const lots = lotsData.objects || [];
  const lotCount = lotsData.count || 0;

  const [createLot, { isLoading: isCreating }] = useCreateLotMutation();
  const [buyLot, { isLoading: isBuying }] = useBuyLotMutation();
  const [deleteLot, { isLoading: isDeleting }] = useDeleteLotMutation();
  const isProcessing = isCreating || isBuying || isDeleting;

  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [purchaseSuccessMessage, setPurchaseSuccessMessage] = useState(null);


  const [formData, setFormData] = useState({
    sell: 'ducats',
    amount: '',
    course: ''
  });
  
  const [formErrors, setFormErrors] = useState({});  
  

  const getMainCharacter = () => {
    return characters?.find(char => char.is_main === true);
  };

  const handleAmountChange = (e) => {
    decimalInputHandler(
      (value) => setFormData(prev => ({ ...prev, amount: value })),
      7, 2, { strip: true }
    )(e);

    if (formErrors.amount) {
      setFormErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors.amount;
        return newErrors;
      });
    }
  };

  const handleCourseChange = (e) => {
    intInputHandler(
      (value) => setFormData(prev => ({ ...prev, course: value })),
      7, { strip: true }
    )(e);

    if (formErrors.course) {
      setFormErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors.course;
        return newErrors;
      });
    }
  };

  const handleSelectChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ 
      ...prev, 
      [name]: value,
      amount: name === 'sell' ? '' : prev.amount
    }));
    
    if (formErrors[name]) {
      setFormErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const validateForm = () => {
    const errors = {};
    
    if (!formData.amount) {
      errors.amount = 'Введите сумму';
    } else {
      const amount = parseFloat(formData.amount);
      if (isNaN(amount) || amount <= 0) {
        errors.amount = 'Введите корректное положительное число';
      }
    }
    
    if (!formData.course) {
      errors.course = 'Введите курс';
    } else {
      const course = parseFloat(formData.course);
      if (isNaN(course) || course <= 0) {
        errors.course = 'Введите корректное положительное число';
      }
    }
    
    return errors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errors = validateForm();
    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }    
    
    setSuccessMessage(null);
    setPurchaseSuccessMessage(null);

    try {
      const amount = parseFloat(formData.amount);
      const course = parseFloat(formData.course);
      
      const lotData = {
        value: Math.round(amount * 100) / 100,
        currency: formData.sell,
        course: Math.round(course)
      };

      const result = await createLot(lotData).unwrap();
      
      if (result) {
        let successInfo;
        if (result.buy_for === 'gold') {
          const ducats = Number(result.ducats);
          const tax = Math.round((ducats * (exchangeSettings?.seller_on_ducats_tax || 0)) * 100) / 100;
          const totalDucats = Math.round((ducats + tax) * 100) / 100;
          successInfo = {
            sellAmount: `${ducats.toFixed(2)} дт.`,
            buyAmount: `${ducats.toFixed(2)} дт.`,
            tax: `${tax.toFixed(2)} дт.`,
            totalDucats: `${totalDucats.toFixed(2)} дт.`,
            sellCurrency: 'ducats',
            buyCurrency: 'gold'
          };
        } else {
          const ducats = Number(result.ducats);
          const tax = Math.round((ducats * (exchangeSettings?.seller_on_ducats_tax || 0)) * 100) / 100;
          successInfo = {
            sellAmount: `${Number(result.gold).toFixed(2)} злт.`,
            buyAmount: `${ducats.toFixed(2)} дт.`,
            tax: `${tax.toFixed(2)} дт.`,
            totalDucats: `${tax.toFixed(2)} дт.`,
            sellCurrency: 'gold',
            buyCurrency: 'ducats'
          };
        }
        
        setSuccessMessage({
          lotNumber: result.number,
          ...successInfo
        });
        
        setFormData({
          sell: 'ducats',
          amount: '',
          course: ''
        });
        
        // Обновляем балансы персонажей в CharactersPage
        dispatch(characterApi.util.invalidateTags(['MyCharacters']));
        
        onSuccess?.('Лот успешно создан!');
      }
    } catch (error) {
      console.error('Create lot error:', error);
      
      if (error?.data) {
        const { error_code, detail, extras } = error.data;
        
        switch (error_code) {
          case 'INSUFFICIENT_FUNDS':
            if (extras && extras.currency) {
              if (extras.currency === 'ducats') {
                setError(`Недостаточно дукатов. Требуется: ${extras.required_amount}, доступно: ${extras.current_amount}`);
              } else if (extras.currency === 'gold') {
                setError(`Недостаточно золота. Требуется: ${extras.required_amount}, доступно: ${extras.current_amount}`);
              } else {
                setError(detail || 'Недостаточно средств для создания лота');
              }
            } else {
              setError('Недостаточно средств для создания лота');
            }
            break;
            
          case 'INVALID_COURSE':
            setError(`Неверный курс обмена. Текущий курс: ${extras?.actual_course?.toFixed(2)}, допустимый диапазон: ${extras?.min_course} - ${extras?.max_course}`);
            break;
            
          case 'SLOT_LIMITS_EXCEEDED':
            if (extras && extras.field) {
              if (extras.field === 'ducats') {
                setError(`Сумма дукатов (${extras.actual_value}) превышает максимальный лимит (${extras.max_value})`);
              } else if (extras.field === 'gold') {
                setError(`Сумма золота (${extras.actual_value}) превышает максимальный лимит (${extras.max_value})`);
              } else {
                setError(detail || 'Превышен лимит для создания лота');
              }
            } else {
              setError('Превышен лимит для создания лота');
            }
            break;

          case 'AMOUNT_BELOW_MINIMUM':
            if (extras && extras.field && extras.min_value) {
              if (extras.field === 'ducats') {
                setError(`Сумма дукатов (${extras.actual_value}) меньше минимальной (${extras.min_value})`);
              } else if (extras.field === 'gold') {
                setError(`Сумма золота (${extras.actual_value}) меньше минимальной (${extras.min_value})`);
              } else {
                setError(detail || 'Сумма меньше минимально допустимой');
              }
            } else {
              setError('Сумма меньше минимально допустимой');
            }
            break;
            
          case 'CANNOT_TRANSACTION_ONLINE_CHARACTER':
            setError('Для создания лота главный персонаж должен быть в оффлайне');
            break;
            
          default:
            setError(detail || 'Ошибка создания лота. Попробуйте позже.');
        }
      } else {
        setError('Ошибка создания лота. Попробуйте позже.');
      }
    }
  };

  const handleBuyLot = async (lot) => {    
    
    try {
      const result = await buyLot(lot.id).unwrap();
      
      if (result && result.success) {
        setPurchaseSuccessMessage({
          lotNumber: lot.number,
          paidAmount: result.amount_paid,
          paidCurrency: result.currency_used,
          receivedAmount: result.amount_received,
          receivedCurrency: result.currency_received
        });
      }
      
      // Обновляем балансы персонажей
      dispatch(characterApi.util.invalidateTags(['MyCharacters']));
      
      onSuccess?.('Покупка успешно совершена!');
      
    } catch (error) {
      console.error('Buy lot error:', error);
      
      if (error?.data) {
        const { error_code, detail, extras } = error.data;
        
        switch (error_code) {
          case 'INSUFFICIENT_FUNDS':
            if (extras && extras.currency) {
              if (extras.currency === 'ducats') {
                setError(`Недостаточно дукатов для покупки. Требуется: ${extras.required_amount}`);
              } else if (extras.currency === 'gold') {
                setError(`Недостаточно золота для покупки. Требуется: ${extras.required_amount}`);
              } else {
                setError(detail || 'Недостаточно средств для покупки лота');
              }
            } else {
              setError('Недостаточно средств для покупки лота');
            }
            break;
            
          case 'CANNOT_TRANSACTION_ONLINE_CHARACTER':
            setError('Для покупки лота главный персонаж должен быть в оффлайне');
            break;
            
          case 'PERMISSION_DENIED':
            setError('Невозможно купить свой же лот');
            break;
            
          case 'MODEL_NOT_FOUND':
            setError('Лот не найден или уже куплен');
            break;
            
          default:
            setError(detail || 'Ошибка покупки лота. Попробуйте позже.');
        }
      } else {
        setError('Ошибка покупки лота. Попробуйте позже.');
      }
    }
  };

  const handleDeleteLot = async (lotId) => {   
    setSuccessMessage(null);
    setPurchaseSuccessMessage(null);
    
    try {
      await deleteLot(lotId).unwrap();
      
      // Обновляем балансы персонажей
      dispatch(characterApi.util.invalidateTags(['MyCharacters']));
      
      onSuccess?.('Лот успешно удален!');
      
    } catch (error) {
      console.error('Delete lot error:', error);
      
      if (error?.data) {
        const { error_code, detail } = error.data;
        
        switch (error_code) {
          case 'MODEL_NOT_FOUND':
            setError('Лот не найден или уже удален');
            break;
            
          case 'CANNOT_TRANSACTION_ONLINE_CHARACTER':
            setError('Для удаления лота главный персонаж должен быть в оффлайне');
            break;
            
          default:
            setError(detail || 'Ошибка удаления лота. Попробуйте позже.');
        }
      } else {
        setError('Ошибка удаления лота. Попробуйте позже.');
      }
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setCurrentPage(1); // Сбрасываем на первую страницу при смене вкладки
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };
  

  const mainCharacter = getMainCharacter();
  const sellOptions = [
    { value: 'ducats', label: 'Дукаты' },
    { value: 'gold', label: 'Золото' }
  ];

  let transactionInfo = null;
  if (formData.amount && formData.course && !formErrors.amount && !formErrors.course) {
    const amount = parseFloat(formData.amount);
    const course = parseFloat(formData.course);
    
    if (!isNaN(amount) && !isNaN(course) && amount > 0 && course >= 0) {
      if (formData.sell === 'ducats') {
        let goldAmount = 0;
        if (course > 0) {
          goldAmount = Math.round((amount / course) * 100) / 100;
        }
        const tax = Math.round((amount * (exchangeSettings?.seller_on_ducats_tax || 0)) * 100) / 100;
        const totalDucats = Math.round((amount + tax) * 100) / 100;
        
        const recalculatedCourse = goldAmount > 0 ? (amount / goldAmount).toFixed(2) : '0.00';
        
        transactionInfo = {
          sellAmount: `${amount.toFixed(2)} дт.`,
          buyAmount: `${goldAmount.toFixed(2)} злт.`,
          tax: `${tax.toFixed(2)} дт.`,
          totalDucats: `${totalDucats.toFixed(2)} дт.`,
          recalculatedCourse: recalculatedCourse
        };
      } else {
        let ducatsAmount = 0;
        if (course > 0) {
          ducatsAmount = Math.round((amount * course) * 100) / 100;
        }
        const tax = Math.round((ducatsAmount * (exchangeSettings?.seller_on_ducats_tax || 0)) * 100) / 100;
        
        const recalculatedCourse = amount > 0 ? (ducatsAmount / amount).toFixed(2) : '0.00';
        
        transactionInfo = {
          sellAmount: `${amount.toFixed(2)} злт.`,
          buyAmount: `${ducatsAmount.toFixed(2)} дт.`,
          tax: `${tax.toFixed(2)} дт.`,
          totalDucats: `${tax.toFixed(2)} дт.`,
          recalculatedCourse: recalculatedCourse
        };
      }
    }
  }

  const totalPages = Math.ceil(lotCount / 10);
  const pageNumbers = [];
  for (let i = 1; i <= totalPages; i++) {
    pageNumbers.push(i);
  }

  return (
    <Card className={styles.exchangeCard}>
      <div className={styles.header}>
        <h2 className={styles.title}>Биржа валюты</h2>
        <Button
          variant="outline"
          size="small"
          onClick={onCancel}
          className={styles.backButton}
        >
          ← Назад
        </Button>
      </div>    

      <div className={styles.content}>
        <div className={styles.infoSection}>
          <h3 className={styles.sectionTitle}>Информация</h3>
          <div className={styles.infoText}>
            <p>Здесь вы можете продавать или покупать игровую валюту (дукаты и золото) у других игроков.</p>
            <p>Все лоты публикуются анонимно и имеют личный номер.</p>
            
            <div className={styles.rules}>
              <p><strong>Вы можете выставить на продажу:</strong></p>
              <ul>
                <li>От <span className={styles.highlight}>{exchangeSettings?.min_ducats_on_slot ?? '...'}</span> <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /> дт. до <span className={styles.highlight}>{exchangeSettings?.max_ducats_on_slot ?? '...'}</span> <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /> дт.</li>
                <li>От <span className={styles.highlight}>{exchangeSettings?.min_gold_on_slot ?? '...'}</span> <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} /> злт. до <span className={styles.highlight}>{exchangeSettings?.max_gold_on_slot ?? '...'}</span> <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} /> злт.</li>
              </ul>
              <p><strong>Курс обмена:</strong> 1 <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} /> злт. = от <span className={styles.highlight}>{exchangeSettings?.min_course_on_gold ?? '...'}</span> <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /> дт. до <span className={styles.highlight}>{exchangeSettings?.max_course_on_gold ?? '...'}</span> <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /> дт.</p>
              <p><strong>Налог продавца:</strong> <span className={styles.highlight}>{((exchangeSettings?.seller_on_ducats_tax || 0) * 100)}%</span> от суммы в <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /> дукатах</p>
            </div>
          </div>
        </div>

        {mainCharacter && (
          <div className={styles.mainCharacterSection}>
            <h3 className={styles.sectionTitle}>Ваш основной персонаж</h3>
            <div className={styles.characterInfo}>
              <div className={styles.characterNameWrapper}>
                <CharacterName name={mainCharacter.name} />
              </div>
              <div className={styles.characterBalances}>
                <div className={styles.balanceItem}>
                  <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} />
                  <span>{Number(mainCharacter.ducats).toFixed(2)} дт.</span>
                </div>
                <div className={styles.balanceItem}>
                  <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} />
                  <span>{Number(mainCharacter.gold).toFixed(2)} злт.</span>
                </div>
                <div className={styles.characterStatus}>
                  <span className={`${styles.statusIndicator} ${mainCharacter.is_online ? styles.online : styles.offline}`}>
                    {mainCharacter.is_online ? 'Онлайн' : 'Оффлайн'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        {error && (
        <div className={styles.errorMessage}>
          {error}
        </div>
      )}

       

        <div className={styles.createLotSection}>
          <h3 className={styles.sectionTitle}>Выставить на биржу игровую валюту</h3>
          <form onSubmit={handleSubmit} className={styles.form}>
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <Select
                  label="Валюта"
                  name="sell"
                  options={sellOptions}
                  value={formData.sell}
                  onChange={handleSelectChange}
                  error={formErrors.sell}
                />
              </div>
              
              <div className={styles.formGroup}>
                <Input
                  label="Сумма"
                  type="text"
                  name="amount"
                  placeholder="0.00"
                  value={formData.amount}
                  onChange={handleAmountChange}
                  error={formErrors.amount}
                />
              </div>
              
              <div className={styles.formGroup}>
                <Input
                  label="Курс (1 злт. = ? дт.)"
                  type="text"
                  name="course"
                  placeholder="0"
                  value={formData.course}
                  onChange={handleCourseChange}
                  error={formErrors.course}
                />
              </div>
            </div>

            {transactionInfo && (
              <div className={styles.transactionInfo}>
                <p>Вы выставляете <span className={styles.highlight}>{transactionInfo.sellAmount}</span> <img src={`/images/currency/${formData.sell === 'ducats' ? 'dt' : 'gld'}.png`} alt={formData.sell === 'ducats' ? 'дт.' : 'злт.'} className={styles.currencyIcon} /> за <span className={styles.highlight}>{transactionInfo.buyAmount}</span> <img src={`/images/currency/${formData.sell === 'ducats' ? 'gld' : 'dt'}.png`} alt={formData.sell === 'ducats' ? 'злт.' : 'дт.'} className={styles.currencyIcon} /></p>
                <p>Налог при совершении сделки: <span className={styles.highlight}>{transactionInfo.tax}</span> <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /></p>
                {formData.sell === 'ducats' ? (
                  <p>Итого для обмена необходимо: <span className={styles.highlight}>{transactionInfo.totalDucats}</span> <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /></p>
                ) : (
                  <p>Итого для обмена необходимо: <span className={styles.highlight}>{transactionInfo.sellAmount}</span> <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} /> и <span className={styles.highlight}>{transactionInfo.tax}</span> <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /></p>
                )}
                <p>Перерасчитанный курс: <span className={styles.highlight}>{transactionInfo.recalculatedCourse}</span> <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /> дт. за 1 <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} /> злт.</p>
              </div>
            )}

            {successMessage && (
              <div className={styles.successMessage}>
                <div className={styles.successHeader}>
                  <span className={styles.successIcon}>✓</span>
                  Лот №{successMessage.lotNumber} успешно создан!
                </div>
                <div className={styles.successDetails}>
                  <p>Лот выставлен на бирже и ожидает подтверждения от продавца.</p>
                  <p>Вы выставили <span className={styles.highlight}>{successMessage.sellAmount}</span> <img src={`/images/currency/${successMessage.sellCurrency === 'ducats' ? 'dt' : 'gld'}.png`} alt={successMessage.sellCurrency === 'ducats' ? 'дт.' : 'злт.'} className={styles.currencyIcon} /> за <span className={styles.highlight}>{successMessage.buyAmount}</span> <img src={`/images/currency/${successMessage.buyCurrency === 'gold' ? 'gld' : 'dt'}.png`} alt={successMessage.buyCurrency === 'gold' ? 'злт.' : 'дт.'} className={styles.currencyIcon} /></p>
                  <p>Налог при совершении сделки: <span className={styles.highlight}>{successMessage.tax}</span> <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /></p>
                  <p>Списано для выставления лота: <span className={styles.highlight}>{successMessage.sellAmount}</span> <img src={`/images/currency/${successMessage.sellCurrency === 'ducats' ? 'dt' : 'gld'}.png`} alt={successMessage.sellCurrency === 'ducats' ? 'дт.' : 'злт.'} className={styles.currencyIcon} />{successMessage.sellCurrency === 'gold' && (
                    <> и <span className={styles.highlight}>{successMessage.tax}</span> <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /></>
                  )}</p>
                </div>
              </div>
            )}

            <div className={styles.actions}>
              <Button
                type="submit"
                variant="primary"
                size="medium"
                disabled={isProcessing}
                className={styles.createButton}
              >
                Создать лот на бирже
              </Button>
            </div>
          </form>
        </div>
        {purchaseSuccessMessage && (
          <div className={styles.successMessage}>
            <div className={styles.successHeader}>
              <span className={styles.successIcon}>✓</span>
              Лот №{purchaseSuccessMessage.lotNumber} успешно куплен!
            </div>
            <div className={styles.successDetails}>
              <p>Вы купили лот №{purchaseSuccessMessage.lotNumber}</p>
              <p>Оплачено: <span className={styles.highlight}>{purchaseSuccessMessage.paidAmount} {purchaseSuccessMessage.paidCurrency === 'gold' ? 'злт.' : 'дт.'}</span> <img src={`/images/currency/${purchaseSuccessMessage.paidCurrency === 'gold' ? 'gld' : 'dt'}.png`} alt={purchaseSuccessMessage.paidCurrency === 'gold' ? 'злт.' : 'дт.'} className={styles.currencyIcon} /></p>
              <p>Получено: <span className={styles.highlight}>{purchaseSuccessMessage.receivedAmount} {purchaseSuccessMessage.receivedCurrency === 'ducats' ? 'дт.' : 'злт.'}</span> <img src={`/images/currency/${purchaseSuccessMessage.receivedCurrency === 'ducats' ? 'dt' : 'gld'}.png`} alt={purchaseSuccessMessage.receivedCurrency === 'ducats' ? 'дт.' : 'злт.'} className={styles.currencyIcon} /></p>
            </div>
          </div>
        )}

        <div className={styles.lotsSection}>
          <h3 className={styles.sectionTitle}>Активные лоты</h3>
          
          <div className={styles.tabs}>
            <Button
              variant={activeTab === 'gold' ? 'primary' : 'outline'}
              size="small"
              onClick={() => handleTabChange('gold')}
              disabled={isProcessing}
              className={styles.tabButton}
            >
              Покупка дукатов
            </Button>
            <Button
              variant={activeTab === 'ducats' ? 'primary' : 'outline'}
              size="small"
              onClick={() => handleTabChange('ducats')}
              disabled={isProcessing}
              className={styles.tabButton}
            >
              Покупка золота
            </Button>
          </div>

          {lots.length > 0 ? (
            <div className={styles.lotsList}>
              {lots.map((lot) => (
                <div key={lot.id} className={styles.lotItem}>
                  <div className={styles.lotInfo}>
                    <div className={styles.lotNumber}>Лот #{lot.number}</div>
                    <div className={styles.lotDetails}>
                      {lot.buy_for === 'gold' ? (
                        <>
                          <div><span className={styles.highlight}>{Number(lot.ducats).toFixed(2)}</span> <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /> дт. за <span className={styles.highlight}>{Number(lot.gold).toFixed(2)}</span> <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} /> злт.</div>
                          <div>Курс: <span className={styles.highlight}>{(Number(lot.ducats) / Number(lot.gold)).toFixed(2)}</span> <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /> дт. за 1 <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} /> злт.</div>
                        </>
                      ) : (
                        <>
                          <div><span className={styles.highlight}>{Number(lot.gold).toFixed(2)}</span> <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} /> злт. за <span className={styles.highlight}>{Number(lot.ducats).toFixed(2)}</span> <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /> дт.</div>
                          <div>Курс: <span className={styles.highlight}>{(Number(lot.ducats) / Number(lot.gold)).toFixed(2)}</span> <img src="/images/currency/dt.png" alt="дт" className={styles.currencyIcon} /> дт. за 1 <img src="/images/currency/gld.png" alt="злт" className={styles.currencyIcon} /> злт.</div>
                        </>
                      )}
                    </div>
                  </div>
                  
                  <div className={styles.lotActions}>
                    {lot.is_owner ? (
                      <Button
                        variant="secondary"
                        size="small"
                        onClick={() => handleDeleteLot(lot.id)}
                        disabled={isProcessing || isBuying}
                        className={styles.deleteButton}
                      >
                        Удалить
                      </Button>
                    ) : (
                      <Button
                        variant="primary"
                        size="small"
                        onClick={() => handleBuyLot(lot)}
                        disabled={isProcessing || isDeleting}
                        className={styles.buyButton}
                      >
                        Купить
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className={styles.noLots}>
              Нет доступных лотов
            </div>
          )}

          {totalPages > 1 && (
            <div className={styles.pagination}>
              {pageNumbers.map((page) => (
                <Button
                  key={page}
                  variant={currentPage === page ? 'primary' : 'outline'}
                  size="small"
                  onClick={() => handlePageChange(page)}
                  disabled={isProcessing || lotsFetching}
                  className={styles.pageButton}
                >
                  {page}
                </Button>
              ))}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};