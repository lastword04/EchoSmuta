import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useLazyGetCharacterByNameQuery } from '../../entities/character/api/characterApi';
import { CharacterInfo } from '../../entities/character/ui/CharacterInfo/CharacterInfo';
import styles from './CharacterSearchPage.module.css';

export const CharacterSearchPage = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchParams, setSearchParams] = useSearchParams();

  // Lazy query: trigger запускается вручную, data/error/isLoading приходят из хука
  const [triggerSearch, { 
    data: character, 
    isLoading, 
    error: queryError,
    isUninitialized 
  }] = useLazyGetCharacterByNameQuery();

  // useRef чтобы избежать повторного trigger при StrictMode
  const hasTriggeredFromUrl = useRef(false);

  // При монтировании читаем параметр из URL и запускаем поиск
  useEffect(() => {
    if (hasTriggeredFromUrl.current) return;
    const savedQuery = searchParams.get('q');
    if (savedQuery) {
      setSearchQuery(savedQuery);
      triggerSearch(savedQuery);
      hasTriggeredFromUrl.current = true;
    }
  }, [searchParams, triggerSearch]);

  // При изменении поиска — обновляем URL (без повторного запуска запроса)
  useEffect(() => {
    if (searchQuery) {
      setSearchParams({ q: searchQuery }, { replace: true });
    } else {
      setSearchParams({}, { replace: true });
    }
  }, [searchQuery, setSearchParams]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      return;
    }
    triggerSearch(searchQuery.trim());
  };

  // Формируем отображаемую ошибку
  const errorMessage = (() => {
    if (!searchQuery.trim() && !isUninitialized && !character) {
      return 'Введите имя персонажа';
    }
    if (queryError?.status === 404) {
      return 'Персонаж не найден';
    }
    if (queryError) {
      return 'Ошибка при поиске персонажа';
    }
    return '';
  })();

  return (
    <div className={styles.page}>
      <form onSubmit={handleSearch} className={styles.searchForm}>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Введите имя персонажа"
          className={styles.searchInput}
        />
        <button type="submit" className={styles.searchButton} disabled={isLoading}>
          Найти
        </button>
      </form>

      {errorMessage && <div className={styles.error}>{errorMessage}</div>}

      {character && <CharacterInfo character={character} />}
    </div>
  );
};