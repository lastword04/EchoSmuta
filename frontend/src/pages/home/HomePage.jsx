// pages/home/HomePage.jsx
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useSelector, useDispatch } from 'react-redux';
import { Card } from '../../shared/ui/Card/Card';

import { Button } from '../../shared/ui/Button/Button';
import { useGetSimpleMeQuery } from '../../entities/character/api/characterApi';
import { toggleMode } from '../../shared/store/modeSlice';
import { setActiveCharacterName } from '../../shared/store/activeCharacterNameSlice';
import withBaseMainPage from '../../shared/hoc/BaseMainPage/withBaseMainPage';
import styles from './HomePage.module.css';

const mockNews = [
  {
    id: 1,
    title: "Новый PvP турнир уже скоро!",
    date: "15 марта 2025",
    content: "Готовьтесь к ежемесячному турниру по PvP! Призовой фонд включает редкие артефакты и золото. Регистрация открыта до 20 марта.",
    image: null
  },
  {
    id: 2,
    title: "Обновление баланса классов",
    date: "12 марта 2025",
    content: "Мы внесли изменения в баланс между классами. Маги получили небольшой баф к урону, а воины - улучшение защиты. Подробности в разделе обновлений.",
    image: null
  },
  {
    id: 3,
    title: "Зимний фестиваль продолжается",
    date: "10 марта 2025",
    content: "Сезонный ивент 'Зимний фестиваль' продлен до конца месяца. Не упустите шанс получить эксклюзивные награды и украшения!",
    image: null
  },
  {
    id: 4,
    title: "Технические работы 17 марта",
    date: "8 марта 2025",
    content: "Плановое техническое обслуживание серверов состоится 17 марта с 03:00 до 06:00 по МСК. Во время работ вход в игру будет недоступен.",
    image: null
  }
];

const HomePageComponent = () => {
  const dispatch = useDispatch();  
  const isNightMode = useSelector((state) => state.local.mode) === 'night';
  const activeCharacterName = useSelector((state) => state.local.activeCharacterName); // ← Из local   
  const navigate = useNavigate();

  const { data: meData } = useGetSimpleMeQuery(undefined, { 
    skip: !!activeCharacterName 
  });

  // Приоритет: Redux кэш → ответ сервера → null
  const heroName = activeCharacterName || meData?.name || null;

  // Сохраняем имя в Redux при первой успешной загрузке
  useEffect(() => {
    if (meData?.name && !activeCharacterName) {
      dispatch(setActiveCharacterName(meData.name));
    }
  }, [meData, activeCharacterName, dispatch]);  
 

  // Toggle function через Redux
  const handleToggleMode = () => {
    dispatch(toggleMode());
  };  

  return (
    <div className={styles.page}>
      <div className={styles.headerDecoration}></div> 
      
             
      <header className={styles.header}>
        <div className={styles.logo}>
          
        </div>
        
        <div className={styles.controls}>
          {/* Приветствие сверху */}
          {heroName && (
            <div className={styles.heroGreeting}>
              <span className={styles.greetingText}>Привет, </span>
              <span className={styles.heroName}>{heroName}</span>
            </div>
          )}
          
          <div className={styles.controlsButtons}>
            <Button
              variant="outline" 
              size="small" 
              onClick={handleToggleMode}
              className={styles.modeToggle}
            >
              {isNightMode ? '☀️ Дневной режим' : '🌙 Ночной режим'}
            </Button>
            
            <Button
              variant="primary" 
              className={styles.authButton}
              onClick={() => navigate(activeCharacterName ? '/characters' : '/login')}
            >
              Войти
            </Button>
            
            <Button
              variant="secondary" 
              className={styles.forumButton}
              onClick={() => window.open('/forum', '_blank')}
            >
              Форум
            </Button>
          </div>
        </div>
      </header>

      {/* Остальная часть компонента без изменений */}
      <main className={styles.main}>
        <div className={styles.content}>
          <section className={styles.hero}>
            <Card className={styles.heroCard}>
              <h2 className={styles.heroTitle}>Добро пожаловать в мир Эха Смуты</h2>
              <p className={styles.heroText}>
                Погрузитесь в легендарный фентезийный мир, хранящий в себе множество тайн. 
                Выбери свой собственный путь и следуй ему. Взгляни в глаза своей судьбе и брось ей вызов! 
                Хватит ли у тебя мужества для того, чтобы узнать правду этого мира и силы воли, 
                чтобы увидеть ее? Всего один шаг отделяет тебя от эха Смуты, ступай же смелее, странник.       
              </p>
              <div className={styles.heroActions}>
                <Button
                  variant="primary" 
                  size="large" 
                  onClick={() => navigate('/register')}
                >
                  Начать игру
                </Button>
              </div>
            </Card>
          </section>

          <section className={styles.newsSection}>
            <h2 className={styles.sectionTitle}>Новости</h2>
            <div className={styles.newsGrid}>
              {mockNews.map(news => (
                <Card key={news.id} className={styles.newsCard}>
                  <div className={styles.newsHeader}>
                    <h3 className={styles.newsTitle}>{news.title}</h3>
                    <span className={styles.newsDate}>{news.date}</span>
                  </div>
                  <p className={styles.newsContent}>{news.content}</p>
                </Card>
              ))}
            </div>
          </section>
        </div>
      </main>
    </div>
  );
};

const HomePage = withBaseMainPage(HomePageComponent);

export { HomePage };