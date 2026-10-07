import { useNavigate } from 'react-router-dom';
import { Card } from '../../shared/ui/Card/Card';
import { Button } from '../../shared/ui/Button/Button';
import { useMemo } from 'react';
import { ForumCard } from '../../entities/forum/ui/ForumCard/ForumCard';
import { useGetAllForumsQuery } from '../../entities/forum/api/forumApi';
import withBaseMainPage from '../../shared/hoc/BaseMainPage/withBaseMainPage';
import styles from './ForumPage.module.css';

const ForumPageComponent = () => {
  const navigate = useNavigate();
  const { 
    data: forums = [], 
    isLoading: loading, 
    isError 
  } = useGetAllForumsQuery();

  const groupedForums = useMemo(() => {
    const grouped = {};
    forums.forEach(item => {
      const section = item.forum.section;
      if (!grouped[section]) {
        grouped[section] = [];
      }
      grouped[section].push(item);
    });
    return grouped;
  }, [forums]);

  const error = isError ? 'Ошибка загрузки форумов. Попробуйте позже.' : null;


const handleEnterForum = (forumId, forumName) => {
  navigate(`/forum/${forumId}/topics`, { 
    state: { forumName } 
  });
};

  const handleBackToHome = () => {
    navigate('/');
  };

  const handleBackToCharacters = () => {
    navigate('/characters');
  };
  const getSectionTitle = (section) => {
    const titles = {
      'game': 'Игровые форумы',
      'moderation': 'Форумы ОСИ',
      'off_topic': 'Оффтопик'
    };
    return titles[section] || section;
  };

  return (
    <div className={styles.page}>
      <div className={styles.content}>
        <Card className={styles.forumCard}>
          <div className={styles.header}>
            <h1 className={styles.title}>Форум</h1>
            <p className={styles.subtitle}>Эхо Смуты</p>
          </div>

          {error && (
            <div className={styles.errorMessage}>
              {error}
            </div>
          )}

          {loading && !forums.length ? (
            <div className={styles.loading}>
              <span>Загрузка форумов...</span>
            </div>
          ) : (
            <div className={styles.forumsContainer}>
              {Object.entries(groupedForums).map(([section, forums]) => (
                <div key={section} className={styles.forumSection}>
                  <h2 className={styles.sectionTitle}>
                    {getSectionTitle(section)}
                  </h2>
                  <div className={styles.forumsGrid}>
                    {forums.map((forum) => (
                      <ForumCard
                        key={forum.forum.id}
                        forum={forum}
                        onEnter={handleEnterForum}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className={styles.footer}>
            <Button
              type="button"
              variant="outline"
              onClick={handleBackToHome}
              className={styles.backButton}
            >
              ← На главную
            </Button>
             <Button
              type="button"
              variant="outline"
              onClick={handleBackToCharacters}
              className={styles.backButton}
            >
              Личный кабинет →
            </Button>
          </div>
        </Card>
      </div>

      
    </div>
  );
};

const ForumPage = withBaseMainPage(ForumPageComponent);

export { ForumPage };