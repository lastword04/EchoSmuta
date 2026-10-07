import { useCallback, useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Card } from '../../shared/ui/Card/Card';
import { Button } from '../../shared/ui/Button/Button';

import { Input } from '../../shared/ui/Input/Input';
import { Select } from '../../shared/ui/Select/Select';
import { config } from '../../shared/config/env/env';
import { generateTemplateName } from '../../entities/file/api/fileApi';
import { useRegisterMutation } from '../../entities/auth/api/authApi';
import { useGetCaptchaMutation } from '../../entities/captcha/api/captchaApi';
import { races, genders, raceDescriptions } from '../../shared/config/character/characterData';
import { useSelector, useDispatch } from 'react-redux';
import { selectVisitId } from '../../entities/auth/store/visitSlice';
import { setActiveCharacterName } from '../../shared/store/activeCharacterNameSlice';
import { setActiveCharacterId } from '../../shared/store/activeCharacterIdSlice';
import { setUserRole } from '../../shared/store/userRoleSlice';
import withBaseMainPage from '../../shared/hoc/BaseMainPage/withBaseMainPage';
import visitService from '../../shared/services/visitService';
import styles from './RegisterPage.module.css';

const RegisterComponentPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const dispatch = useDispatch();
  
  const [formData, setFormData] = useState({
    characterName: '',
    email: '',
    password: '',
    confirmPassword: '',
    race: '',
    gender: '',
    discoverySource: '',
    agreeToTerms: false,
    captchaInput: ''
  });
    
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const templateName = formData.race && formData.gender
    ? generateTemplateName(formData.race, formData.gender)
    : null;
  const characterImage = templateName
    ? `${config.FILE_API_BASE_URL}/template_name/${templateName}/content`
    : null;
  
  const [captchaData, setCaptchaData] = useState(null);
  const [referralCode, setReferralCode] = useState(null);
  const visitId = useSelector(selectVisitId);
  const [loadCaptcha] = useGetCaptchaMutation();
  const [register] = useRegisterMutation();

  // Загрузка капчи через RTK Query; возвращает данные, при ошибке бросает исключение
  const fetchCaptcha = useCallback(async () => {
    return await loadCaptcha().unwrap();
  }, [loadCaptcha]);

  // Получаем реферальный код из URL параметров
  useEffect(() => {
    const refParam = searchParams.get('ref');
    if (refParam) {
      // Декодируем URL и заменяем + на пробелы
      const decodedRef = decodeURIComponent(refParam).replace(/\+/g, ' ');
      setReferralCode(decodedRef);
    }
  }, [searchParams]);

  useEffect(() => {
    const loadCaptchaData = async () => {
      try {
        const data = await fetchCaptcha();
        setCaptchaData(data);
      } catch (error) {
        console.error('Failed to load captcha:', error);
        setErrors(prev => ({
          ...prev,
          captcha: 'Ошибка загрузки капчи. Попробуйте обновить страницу.'
        }));
      }
    };

    loadCaptchaData();
  }, [fetchCaptcha]);

  // Новая капча — чистый ввод (как в WorkshopView)
  useEffect(() => {
    if (captchaData) setFormData(prev => ({ ...prev, captchaInput: '' }));
  }, [captchaData]);

 

  const clearError = (fieldName) => {
    if (errors[fieldName] || errors.general) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[fieldName];
        delete newErrors.general;
        return newErrors;
      });
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
    
    clearError(name);
  };

  const handleSelectChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    clearError(name);
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.characterName.trim()) {
      newErrors.characterName = 'Введите имя персонажа';
    } else if (formData.characterName.length < 2) {
      newErrors.characterName = 'Имя персонажа не должно быть меньше 2 символов';
    }else if (formData.characterName.length > 21) {
      newErrors.characterName = 'Имя персонажа не должно превышать 21 символ';
    } else {
      if (!/^[a-zA-Zа-яА-ЯёЁ0-9\s]+$/.test(formData.characterName)) {
        newErrors.characterName = 'Никнейм может содержать только буквы, цифры и пробелы';
      } else if (/[a-zA-Z]/.test(formData.characterName) && /[а-яА-ЯёЁ]/.test(formData.characterName)) {
        newErrors.characterName = 'Никнейм должен содержать буквы только одного языка (русские или латинские)';
      } else if (!formData.characterName.trim()) {
        newErrors.characterName = 'Имя персонажа не может состоять только из пробелов';
      }
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Введите email';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Неверный формат email';
    }
    
    if (!formData.password) {
      newErrors.password = 'Введите пароль';
    }
    // TODO: uncommit this in production
    // } else if (formData.password.length < 8) {
    //   newErrors.password = 'Пароль должен содержать минимум 8 символов';
    // }
    
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Подтвердите пароль';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Пароли не совпадают';
    }
    
    if (!formData.race) {
      newErrors.race = 'Выберите расу';
    }
    
    if (!formData.gender) {
      newErrors.gender = 'Выберите пол';
    }
    
    if (!formData.agreeToTerms) {
      newErrors.agreeToTerms = 'Необходимо согласиться с пользовательским соглашением и правилами проекта';
    }

    if (!formData.captchaInput.trim()) {
      newErrors.captchaInput = 'Введите код с картинки';
    } else if (!captchaData) {
      newErrors.captcha = 'Капча не загружена. Попробуйте обновить страницу.';
    }
    
    return newErrors;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const newErrors = validateForm();
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    
    setErrors({});
    setIsLoading(true);
    
    try {
      // Подготовка данных для отправки
      const fingerprint = await visitService.getFingerprint();
      const registrationData = {
        email: formData.email,
        password: formData.password,
        source_of_knowledge: formData.discoverySource,
        name: formData.characterName,
        race: formData.race,
        is_male: formData.gender === 'male',
        captcha_id: captchaData?.captcha_id,
        user_input: formData.captchaInput,
        visit_id: visitId,
        fingerprint: fingerprint,
        ...(referralCode && { referral_code: referralCode }) // Добавляем реферальный код если он есть
      };
      
      // Отправка данных на сервер
      const registeredCharacter = await register(registrationData).unwrap();
      
      dispatch(setActiveCharacterName(registeredCharacter.name));
      dispatch(setActiveCharacterId(registeredCharacter.id));
      // Новый пользователь всегда не-админ (значение UserRole.USER с бэкенда)
      dispatch(setUserRole('user'));

      navigate('/location');
      
    } catch (error) {
      if (error?.data) {
        const { status } = error;
        const { data } = error;
        
        if (status === 422) {
          if (data.extras?.field === 'captcha') {
            setErrors({
              captchaInput: 'Неверный код с картинки. Попробуйте еще раз.'
            });
            // Перезагружаем капчу
            const newCaptcha = await fetchCaptcha();
            setCaptchaData(newCaptcha);
          } else {
            setErrors({
              general: 'Пожалуйста, проверьте правильность заполнения формы'
            });
          }
        } else if (status === 410) {
          // Капча просрочена (GONE)
          setErrors({
            captchaInput: 'Введена просроченная капча. Попробуйте снова.'
          });
          // Перезагружаем капчу
          const newCaptcha = await fetchCaptcha();
          setCaptchaData(newCaptcha);
        } else if (status === 400) {
          // Неверный ввод капчи
          if (data.error_code === 'INVALID_CAPTCHA_INPUT') {
            setErrors({
              captchaInput: 'Введена неверная капча. Попробуйте снова.'
            });
            // Перезагружаем капчу
            const newCaptcha = await fetchCaptcha();
            setCaptchaData(newCaptcha);
          } else {
            setErrors({
              general: 'Ошибка валидации данных. Проверьте введённые данные.'
            });
          }
        } else if (status === 409) {
          // Конфликт данных (дубликаты)
          if (data.extras?.field === 'email') {
            setErrors({
              email: 'Пользователь с таким email уже существует'
            });
          } else if (data.extras?.field === 'name') {
            setErrors({
              characterName: 'Персонаж с таким именем уже существует'
            });
          } else {
            setErrors({
              general: 'Пользователь с такими данными уже существует'
            });
          }
        } else {
          setErrors({
            general: 'Ошибка регистрации. Попробуйте позже.'
          });
        }
      } else {
        setErrors({
          general: 'Ошибка подключения к серверу. Попробуйте позже.'
        });
      }
      
      // Перезагружаем капчу при ошибке (кроме ошибок валидации формы)
      if (error?.status !== 422 || 
          (error?.data?.extras?.field !== 'email' && 
           error?.data?.extras?.field !== 'name')) {
        try {
          const newCaptcha = await fetchCaptcha();
          setCaptchaData(newCaptcha);
          setFormData(prev => ({ ...prev, captchaInput: '' })); // Очищаем поле ввода
        } catch (captchaError) {
          console.error('Failed to reload captcha:', captchaError);
        }
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleReloadCaptcha = async () => {
    try {
      const data = await fetchCaptcha();
      setCaptchaData(data);
      setFormData(prev => ({ ...prev, captchaInput: '' })); // Очищаем поле ввода
      clearError('captchaInput');
      clearError('captcha');
    } catch (error) {
      console.error('Failed to reload captcha:', error);
      setErrors(prev => ({
        ...prev,
        captcha: 'Ошибка загрузки капчи. Попробуйте позже.'
      }));
    }
  };

  const handleBackToLogin = () => {
    navigate('/login');
  };

  return (
    <div className={styles.page}>
      
      <div className={styles.content}>
        <Card className={styles.registerCard}>
          <div className={styles.header}>
            <h1 className={styles.title}>Регистрация</h1>
            <p className={styles.subtitle}>Эхо Смуты</p>
          </div>

          {referralCode && (
            <div className={styles.referralInfo}>
              <p>Регистрация по реферальной ссылке: <strong>{referralCode}</strong></p>
            </div>
          )}

          {errors.general && (
            <div className={styles.generalError}>
              {errors.general}
            </div>
          )}

          <form onSubmit={handleSubmit} className={styles.form}>
            <div className={styles.formSection}>
              <h3 className={styles.sectionTitle}>Основная информация</h3>
                        <div className={styles.inputWrapper}>
              
               <Input
              label="Имя персонажа"
              type="text"
              name="characterName"
              placeholder="Только русские или латинские буквы, цифры, максимум 21 символ"
              value={formData.characterName}
              onChange={(e) => {
                if (e.target.value.length <= 21) {
                  handleInputChange(e);
                }
              }}
              error={errors.characterName}
            />
            <div className={styles.charCounter}>
                          {formData.characterName.length} / 21
                        </div>
          </div>


              <Input
                label="Email"
                type="email"
                name="email"
                placeholder="your@email.com"
                value={formData.email}
                onChange={handleInputChange}
                error={errors.email}
                autoComplete="email"
              />

              <Input
                label="Пароль"
                type="password"
                name="password"
                placeholder="Минимум 8 символов"
                value={formData.password}
                onChange={handleInputChange}
                error={errors.password}
                autoComplete="new-password"
              />

              <Input
                label="Подтвердите пароль"
                type="password"
                name="confirmPassword"
                placeholder="Повторите пароль"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                error={errors.confirmPassword}
                autoComplete="new-password"
              />
            </div>

            <div className={styles.formSection}>
              <h3 className={styles.sectionTitle}>Персонаж</h3>
              
              <div className={styles.characterSelection}>
                <Select
                  label="Раса"
                  name="race"
                  options={races}
                  value={formData.race}
                  onChange={handleSelectChange}
                  error={errors.race}
                />

                {formData.race && raceDescriptions[formData.race] && (
                  <div className={styles.raceDescription}>
                    <h4 className={styles.raceTitle}>
                      {races.find(r => r.value === formData.race)?.label}
                    </h4>
                    <p className={styles.raceText}>
                      {raceDescriptions[formData.race]}
                    </p>
                  </div>
                )}

                <Select
                  label="Пол"
                  name="gender"
                  options={genders}
                  value={formData.gender}
                  onChange={handleSelectChange}
                  error={errors.gender}
                />

                {/* Отображение изображения персонажа */}
                {(formData.race && formData.gender) && (
                  <div className={styles.characterPreview}>
                      <img 
                        src={characterImage}
                        alt={`${races.find(r => r.value === formData.race)?.label} ${genders.find(g => g.value === formData.gender)?.label}`}
                        className={styles.characterImage}
                        onError={(e) => {
                          e.currentTarget.onerror = null;
                          e.currentTarget.src = '/images/city-trade/no-image.png';
                        }}
                      />
                  </div>
                )}
              </div>
            </div>

            <div className={styles.formSection}>
              <h3 className={styles.sectionTitle}>Дополнительно</h3>
              
             <Input
                label="Как Вы узнали про Эхо Смуты?"
                type="text"
                name="discoverySource"
                placeholder="Расскажите, как вы узнали о нашей игре..."
                value={formData.discoverySource}
                onChange={handleInputChange}
                error={errors.discoverySource}
              />
            </div>

            {/* Обновленная секция капчи */}
            <div className={styles.captchaSection}>
              <h3 className={styles.sectionTitle}>Защита от ботов</h3>
              
              {errors.captcha ? (
                <div className={styles.captchaError}>
                  <span>Капча не загружена</span>
                  <Button
                    type="button"
                    variant="outline"
                    size="small"
                    onClick={handleReloadCaptcha}
                    className={styles.retryCaptchaButton}
                  >
                    Попробовать снова
                  </Button>
                </div>
              ) : (               
                <div className={styles.captchaRow}>
                  <div
                    className={styles.captchaImageWrapper}
                    onClick={captchaData ? handleReloadCaptcha : undefined}
                    title={captchaData ? "Нажмите для обновления капчи" : ""}
                  >
                    {captchaData ? (
                      <img
                        src={captchaData.image_url}
                        alt="Капча"
                        className={styles.captchaImage}
                      />
                    ) : (
                      <div className={styles.captchaImagePlaceholder} />
                    )}
                  </div>

                  <div className={styles.captchaInputContainer}>
                    <Input
                      label="Введите код"
                      type="text"
                      name="captchaInput"
                      placeholder="Код с картинки"
                      value={formData.captchaInput}
                      onChange={handleInputChange}
                      error={errors.captchaInput || errors.captcha}
                      autoComplete="off"
                      disabled={!captchaData}
                    />
                  </div>
                </div>                
              )}
            </div>

            <div className={styles.agreementSection}>
              <div className={styles.agreementCheckbox}>
                <input
                  type="checkbox"
                  id="agreeToTerms"
                  name="agreeToTerms"
                  checked={formData.agreeToTerms}
                  onChange={handleInputChange}
                />
                <label htmlFor="agreeToTerms">
                  Регистрируясь, вы подтверждаете, что ознакомились и согласны с{' '}
                  <a href="#" target="_blank" rel="noopener noreferrer">
                    пользовательским соглашением
                  </a>{' '}
                  и{' '}
                  <a href="#" target="_blank" rel="noopener noreferrer">
                    правилами проекта
                  </a>
                </label>
              </div>
              {errors.agreeToTerms && (
                <div className={styles.agreementError}>
                  {errors.agreeToTerms}
                </div>
              )}
            </div>
              {Object.keys(errors).length > 0 && (
              <div className={styles.formErrors}>
                <div className={styles.formErrorsIcon}>⚠️</div>
                <div className={styles.formErrorsContent}>
                  <div className={styles.formErrorsTitle}>Пожалуйста, исправьте следующие ошибки:</div>
                  <ul className={styles.formErrorsList}>
                    {Object.entries(errors).map(([field, message]) => {
                      // Не показываем технические ошибки и ошибки, которые уже отображены
                      if (field === 'general' || field === 'agreeToTerms') return null;
                      return <li key={field}>{message}</li>;
                    })}
                    {errors.agreeToTerms && <li>{errors.agreeToTerms}</li>}
                  </ul>
                </div>
              </div>
            )}
            <div className={styles.actions}>
              <Button
                type="submit"
                variant="primary"
                size="large"
                disabled={isLoading}
                className={styles.submitButton}
              >
                {isLoading ? 'Регистрация...' : 'Зарегистрироваться'}
              </Button>
            </div>
          </form>

          <div className={styles.footer}>
            <p className={styles.hasAccount}>
              Уже есть аккаунт?{' '}
              <button
                type="button"
                onClick={handleBackToLogin}
                className={styles.loginLink}
              >
                Войдите
              </button>
            </p>
            
            <button
              type="button"
              onClick={() => navigate('/')}
              className={styles.backToHome}
            >
              ← Вернуться на главную
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
};

const RegisterPage = withBaseMainPage(RegisterComponentPage);

export { RegisterPage }