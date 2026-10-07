import { Card } from '../../shared/ui/Card/Card';
import { Button } from '../../shared/ui/Button/Button';
import { useGetReferralLinkQuery } from '../../entities/character/api/characterApi';
import withBaseMainPage from '../../shared/hoc/BaseMainPage/withBaseMainPage';
import { parseUtcDate } from '../../shared/lib/utils/utcDate';
import styles from './ReferralsPage.module.css';

const ReferralsPageComponent = () => {
  
  // Дефолтные значения для мгновенного рендера
  const { data: referralData = { url: '', current_uses: 0, max_uses: null, referrals: [] }, isError, refetch } = useGetReferralLinkQuery();

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      console.log('Реферальная ссылка скопирована в буфер обмена!');
    }).catch(err => {
      console.error('Failed to copy: ', err);
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      console.log('Реферальная ссылка скопирована в буфер обмена!');
    });
  };

  if (isError) {
    return (
      <div className={styles.page}>
        <div className={styles.content}>
          <Card className={styles.errorCard}>
            <div className={styles.errorMessage}>
              Ошибка загрузки реферальных данных.
            </div>
            <Button
              variant="outline"
              size="medium"
              onClick={() => refetch()}
            >
              Повторить попытку
            </Button>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.page}>      
      <div className={styles.content}>
        <Card className={styles.referralsCard}>
          <div className={styles.header}>
            <h1 className={styles.title}>Реферальная программа</h1>
          </div>

          <div className={styles.infoSection}>
            <p>Вы находитесь в системе управления рефералами.</p>
            <p>Здесь вы можете получить необходимую информацию для того, чтобы начать привлекать ваших друзей и знакомых в Эхо Смуты.</p>
            
            <div className={styles.benefits}>
              <p><strong>За каждый взятый уровень вашим рефералом (начиная с 5-го) вы получаете База уровня × 5 опыта.</strong></p>
              <p><strong>Ваш реферал за каждый взятый уровень получает База уровня × 5 дукатов.</strong></p>
              <p><a href="/experience-table" target="_blank" rel="noopener noreferrer">Ознакомиться со значением Базы уровня вы можете на странице Tаблица опыта</a></p>
            </div>
          </div>

          <div className={styles.referralSection}>
            <h2 className={styles.sectionTitle}>Ваша реферальная ссылка</h2>
            
            <div className={styles.referralInfo}>
              <div className={styles.referralLinkContainer}>
                <input
                  type="text"
                  value={referralData.url}
                  readOnly
                  className={styles.referralLink}
                />
                <Button
                  variant="primary"
                  size="medium"
                  onClick={() => copyToClipboard(referralData.url)}
                  className={styles.copyButton}
                >
                  Копировать
                </Button>
              </div>
              
              <div className={styles.referralStats}>
                <p><strong>Количество приглашенных рефералов:</strong> {referralData.current_uses}</p>
                {referralData.max_uses && (
                  <p><strong>Максимальное количество использований:</strong> {referralData.max_uses}</p>
                )}
              </div>
            </div>
          </div>

          {referralData.referrals && referralData.referrals.length > 0 && (
            <div className={styles.referralsListSection}>
              <h2 className={styles.sectionTitle}>Ваши рефералы</h2>
              <div className={styles.referralsList}>
                {referralData.referrals.map((referral, index) => (
                  <div key={referral.id} className={styles.referralItem}>
                    <span className={styles.referralNumber}>#{index + 1}</span>
                    <span className={styles.referralName}>{referral.referred_user_name}</span>
                    <span className={styles.referralDate}>
                      {parseUtcDate(referral.created_at).toLocaleDateString('ru-RU')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

const ReferralsPage = withBaseMainPage(ReferralsPageComponent);

export { ReferralsPage };