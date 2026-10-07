import { useEffect, useRef, useState, useLayoutEffect, memo, useMemo, useCallback } from 'react';
import DOMPurify from 'dompurify';
import styles from './ChatContent.module.css';
import { fetchBellMapCached, fetchBellSizesCached, getBellMapSync, getBellSizesSync } from '../../../../entities/chat/lib/bellsData';
import { parseSmileys, parseMentions, parseUrls, isYouTube } from './messageParser';



// Мемоизированный компонент сообщения
const ChatMessage = memo(({ 
  msg, 
  index, 
  settings, 
  currentUserId, 
  roomId, 
  bellMap,
  bellSizes,
  onCharacterClick,
  onContextMenu,
  onSmileyClick 
}) => {
  const getTimeColor = (message) => {
    const isSender = message.user_id === currentUserId;
    const isRecipient = message.target_user_ids?.includes(currentUserId);
    
    if (message.room === 'private') {
      if (isSender) return '#b90000';
      if (isRecipient) return '#fb0202';
      return null;
    } else if (message.room === 'clan') {
      if (isSender) return settings.clan_chat_is_blue ? '#001780' : '#b90000';
      if (isRecipient) return settings.clan_chat_is_blue ? '#294ef6' : '#fb0202';
      return null;
    } else if (message.room === 'system') {
      return '#8b0000';
    } else if (message.is_trade) {
      return isSender ? '#800080' : '#b16cb1';
    } else if (message.room === roomId) {
      if (isSender) return '#af7a07';
      if (isRecipient) return '#d7980d';
      return '#dfb56e';
    } else {
      if (isSender) return '#658748';
      if (isRecipient) return '#6bbb40';
      return null;
    }
  };


// 1. СНАЧАЛА вспомогательные функции
const processUrls = useCallback((text) => {
  const parts = [];
  let lastIndex = 0;
  
  const urls = parseUrls(text);
  
  urls.forEach(urlMatch => {
    if (urlMatch.index > lastIndex) {
      parts.push(text.substring(lastIndex, urlMatch.index));
    }
    
    const url = urlMatch.url;
    const isYouTubeLink = isYouTube(url);
    
    if (isYouTubeLink) {
      parts.push(
        <img
          key={`yticon-${urlMatch.index}`}
          src="/images/icons/youtube.png"
          alt="YouTube"
          className={styles.youtubeIcon}
          style={{
            width: '14px',
            height: '14px',
            marginRight: '4px',
            verticalAlign: 'middle',
          }}
        />
      );
    }
    
    parts.push(
      <a
        key={`url-${urlMatch.index}`}
        href={url.startsWith('http') ? url : `https://${url}`}
        target="_blank"
        rel="noopener noreferrer"
        style={{
          color: '#8b0000',
          textDecoration: 'underline',
        }}
      >
        {url}
      </a>
    );
    
    lastIndex = urlMatch.index + urlMatch.fullMatch.length;
  });
  
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }
  
  return parts;
}, []);

// 2. ПОТОМ функция, которая использует processUrls
const processTextWithMentionsAndUrls = useCallback((inputText) => {
  const finalParts = [];
  let lastIndex = 0;
  
  const mentions = parseMentions(inputText);
  const mentionParts = [];
  
  mentions.forEach(mention => {
    mentionParts.push({
      type: 'mention',
      index: mention.index,
      fullMatch: mention.fullMatch,
      name: mention.name,
      id: mention.id,
    });
  });
  
  mentionParts.sort((a, b) => a.index - b.index);
  
  mentionParts.forEach(mention => {
    if (mention.index > lastIndex) {
      const preText = inputText.substring(lastIndex, mention.index);
      finalParts.push(...processUrls(preText));
    }
    
    finalParts.push(
      <span
        key={`mention-${mention.id}-${mention.index}`}
        className={styles.chatUser}
        onClick={() => onCharacterClick(mention.name, mention.id)}
        onContextMenu={(e) => onContextMenu(e, mention.name, mention.id)}
        style={{ cursor: 'pointer' }}
      >
        {mention.name}
      </span>
    );
    
    lastIndex = mention.index + mention.fullMatch.length;
  });
  
  if (lastIndex < inputText.length) {
    const remainingText = inputText.substring(lastIndex);
    finalParts.push(...processUrls(remainingText));
  }
  
  return finalParts;
}, [onCharacterClick, onContextMenu, processUrls]); // ✅ Добавил processUrls

// 3. И ТОЛЬКО ПОТОМ основная функция
const parseMessageText = useCallback((text = '') => {
  if (!text) return '';
  
  const parts = [];
  let lastIndex = 0;
  
  const smileys = parseSmileys(text);
  
  smileys.forEach(smiley => {
    if (smiley.index > lastIndex) {
      const preText = text.substring(lastIndex, smiley.index);
      parts.push(...processTextWithMentionsAndUrls(preText));
    }
    
    const folder = bellMap[smiley.smileyNumber] || 'Emotions';
    const size = bellSizes[smiley.smileyNumber];
    parts.push(
      <img
        key={`smiley-${smiley.smileyNumber}-${smiley.index}`}
        src={`/images/bells/${folder}/${smiley.smileyNumber}.gif`}
        className={styles.smileyImage}
        {...(size ? { width: size[0], height: size[1] } : {})}
        onClick={() => onSmileyClick(`|${smiley.smileyNumber}|`)}
        loading="eager"
      />
    );
    
    lastIndex = smiley.index + smiley.fullMatch.length;
  });
  
  if (lastIndex < text.length) {
    parts.push(...processTextWithMentionsAndUrls(text.substring(lastIndex)));
  }
  
  return parts;
}, [bellMap, bellSizes, onSmileyClick, processTextWithMentionsAndUrls]);


  // ✅ КЭШ: парсим текст ОДИН раз на сообщение, а не при каждом рендере
  const parsedContent = useMemo(
    () => parseMessageText(msg.text || ''),
    [msg.text, parseMessageText]
  );

  const sanitizeSystemText = useCallback((text) => {
    if (!text) return '';
    
    // DOMPurify уже санитизирует, добавляем стили для ссылок через regex
    const clean = DOMPurify.sanitize(text, {
      USE_PROFILES: { html: true },
      ALLOWED_TAGS: ['b', 'i', 'u', 'a', 'br', 'span', 'strong', 'em'],
      ALLOWED_ATTR: ['href', 'target', 'rel', 'style']
    });
    
    // Добавляем стили к ссылкам через regex (без DOM)
    return clean.replace(
      /<a([^>]*)>/g,
      (match, attrs) => {
        const hasTarget = /target=/.test(attrs);
        const hasRel = /rel=/.test(attrs);
        const style = 'style="color: #8b0000;"';
        const target = hasTarget ? '' : ' target="_blank"';
        const rel = hasRel ? '' : ' rel="noopener noreferrer"';
        return `<a${attrs}${target}${rel} ${style}>`;
      }
    );
  }, []);

  const renderPrivateInfo = useCallback((msg) => {
    if (msg.room !== 'private' || !msg.target_user_names?.length) return null;

    const recipients = msg.target_user_names.map((name, i) => {
      const id = msg.target_user_ids?.[i];
      const isLast = i === msg.target_user_names.length - 1;

      return (
        <span key={`recipient-${id || name}-${i}`}>
          <span className={styles.chatUser}
          onClick={() => onCharacterClick(name, id, true)}
          onContextMenu={(e) => onContextMenu(e, name, id)}
          style={{ color: '#b90000' }}
          >
          {name}
        </span>
        {!isLast && ' '}
        </span>
      );
    });

    return (
      <>
        <span style={{ color: '#b90000'}}> лично: </span>
        {recipients}
      </>
    );
  }, [onCharacterClick, onContextMenu]);

  const renderMentions = useCallback((msg) => {
    if (msg.room === 'private' || !msg.target_user_names?.length) return null;

    const mentions = msg.target_user_names.map((name, i) => {
      const id = msg.target_user_ids?.[i];
      const isLast = i === msg.target_user_names.length - 1;

      return (
        <span key={`mention-wrapper-${id || name}-${i}`}>
          <span
            className={styles.chatUser}
            onClick={() => onCharacterClick(name, id, false)}
            onContextMenu={(e) => onContextMenu(e, name, id)}
            style={{ cursor: 'pointer' }}
          >
            {name}
          </span>
          {!isLast && ' '}
        </span>
      );
    });

    return <>{mentions}</>;
  }, [onCharacterClick, onContextMenu]);

  if (msg.room === 'system') {
    const safeHtml = sanitizeSystemText(msg.text);
    const isCreateCharacter = msg.message_type === 'system_create_character';
    const isSystemPrivate = msg.message_type === 'system_private' || msg.message_type === 'system_play_character';

    return (
      <div key={index} className={styles.chatMessage}>
        <span
          className={styles.chatTime}
          style={{ 
            backgroundColor: isSystemPrivate ? '#4c2727' : 'transparent', 
            color: isSystemPrivate ? '#ffffff' : '#000000'
          }}
        >
          {msg.time}
        </span>{" "}
        {msg.message_type === 'system_play_character' && msg.target_user_names?.length > 0 && (
          <>
            <span
              className={styles.chatUser}
              onClick={() => onCharacterClick(msg.user, msg.user_id)}
              onContextMenu={(e) => onContextMenu(e, msg.user, msg.user_id)}
              style={{
                color: '#4c2727',
                fontWeight: 'bold',
                cursor: 'pointer',
              }}
            >
              {msg.user}
            </span>{" "}
          </>
        )}
        <span
          className={styles.chatText}
          style={{
            color: '#8b0000',
            fontWeight: 'bold',
            fontStyle: settings?.system_italic ? 'italic' : 'normal',
          }}
          dangerouslySetInnerHTML={{ __html: safeHtml }}
        />
        {isCreateCharacter && (
          <>
            {' '}
            <a
              href="#"
              onClick={(e) => e.preventDefault()}
              style={{
                color: '#8b0000',
                fontWeight: 'bold',
                textDecoration: 'underline',
                cursor: 'pointer',
              }}
            >
              Заблокировать
            </a>
          </>
        )}
      </div>
    );
  }

  const timeColor = getTimeColor(msg);
  const hasBackgroundColor = timeColor !== null;
  const isPrivate = msg.room === 'private';
  const hasMentions = !isPrivate && msg.target_user_names?.length > 0;

  return (
    <div key={index} className={styles.chatMessage}>
      <span 
        className={styles.chatTime} 
        style={{
          backgroundColor: hasBackgroundColor ? timeColor : 'transparent',
          color: hasBackgroundColor ? '#ffffff' : '#000000'
        }}
      >
        {msg.time}
      </span>{" "}
      
      <strong
        className={styles.chatUser}
        onClick={() => onCharacterClick(msg.user, msg.user_id, msg.room === 'private')}
        onContextMenu={(e) => onContextMenu(e, msg.user, msg.user_id)}
        style={{
          color: msg.is_trade
            ? getTimeColor(msg)
            : isPrivate
            ? '#b90000'
            : '#000000',
          cursor: 'pointer',
        }}
      >
        {msg.user}
      </strong>
      
      {(() => {
        const isSelfMessage =
          msg.target_user_ids?.length === 1 &&
          msg.target_user_ids[0] === msg.user_id;

        const textStyle = {
          fontStyle:
            msg.room === 'private' && msg.message_type === 'ignore'
              ? 'italic'
              : 'normal',
        };

        if (isSelfMessage) {
          if (isPrivate) {
            return (
              <span
                className={styles.chatText}
                style={{
                  ...textStyle,
                  color: '#b90000',
                }}
              >
                {' '}сам себе:{' '}
                {parsedContent}
              </span>
            );
          } else {
            return (
              <span className={styles.chatText} style={textStyle}>
                {' '}пробормотал под нос:{' '}
                {parsedContent}
              </span>
            );
          }
        }

        if (isPrivate) {
          return (
            <>
              {renderPrivateInfo(msg)}
              <span className={styles.chatText} style={textStyle}>
                {' '}
                {parsedContent}
              </span>
            </>
          );
        }

        if (hasMentions) {
          return (
            <>
              {': '}
              {renderMentions(msg)}
              <span className={styles.chatText} style={textStyle}>
                {' '}
                {parsedContent}
              </span>
            </>
          );
        }

        return (
          <span className={styles.chatText} style={textStyle}>
            {': '}
            {parsedContent}
          </span>
        );
      })()}
    </div>
  );
}, (prevProps, nextProps) => {
  // Кастомное сравнение для memo:
  // сравниваем ПО ПОЛЯМ, а не по ссылке на объект msg —
  // RTK Query после invalidateTags возвращает новые объекты,
  // и сравнение по === всегда давало бы false (memo не работал)
  return (
    prevProps.msg.id === nextProps.msg.id &&
    prevProps.msg.text === nextProps.msg.text &&
    prevProps.msg.time === nextProps.msg.time &&
    prevProps.msg.room === nextProps.msg.room &&
    prevProps.msg.is_trade === nextProps.msg.is_trade &&
    prevProps.msg.message_type === nextProps.msg.message_type &&
    prevProps.bellSizes === nextProps.bellSizes &&
    prevProps.settings.font_size === nextProps.settings.font_size &&
    prevProps.settings.clan_chat_is_blue === nextProps.settings.clan_chat_is_blue &&
    prevProps.settings.system_italic === nextProps.settings.system_italic
  );
});

const ChatContent = ({ settings, messages, onCharacterClick, currentUserId, roomId }) => {
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const [bellMap, setBellMap] = useState(getBellMapSync());
  const [bellSizes, setBellSizes] = useState(getBellSizesSync());
  const [contextMenu, setContextMenu] = useState({
    visible: false,
    x: 0,
    y: 0,
    characterName: '',
    characterId: ''
  });

  useEffect(() => {
    const loadBellData = async () => {
      try {
        const [map, sizes] = await Promise.all([
          fetchBellMapCached(),
          fetchBellSizesCached(),
        ]);
        setBellMap(map);
        setBellSizes(sizes);
      } catch (error) {
        console.error('Ошибка загрузки маппинга смайликов:', error);
      }
    };
    loadBellData();
  }, []);

  // --- Автоскролл, только если пользователь внизу ---
  const [isUserNearBottom, setIsUserNearBottom] = useState(true);

  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const threshold = 80; // пикселей до низа
      const distanceFromBottom =
        container.scrollHeight - container.scrollTop - container.clientHeight;
      setIsUserNearBottom(distanceFromBottom < threshold);
    };

    container.addEventListener('scroll', handleScroll, { passive: true });
    return () => container.removeEventListener('scroll', handleScroll);
  }, []);



    // Асинхронная доводка скролла после загрузки новых смайликов
  // НЕ блокирует paint, работает после коммита React
  useEffect(() => {
    if (!isUserNearBottom) return;
    
    const container = messagesContainerRef.current;
    if (!container) return;

    // Берём ТОЛЬКО картинки из последнего сообщения, а не все в контейнере
    const messages = container.querySelectorAll(`.${styles.chatMessage}`);
    const lastMessage = messages[messages.length - 1];
    if (!lastMessage) return;
    
    const newImages = lastMessage.querySelectorAll('img:not([data-loaded])');
    if (newImages.length === 0) return;

    const promises = Array.from(newImages).map(img => {
      if (img.complete) return Promise.resolve();
      return new Promise(resolve => {
        img.onload = resolve;
        img.onerror = resolve;
        img.dataset.loaded = '1';  // помечаем чтобы не ждать повторно
      });
    });

    Promise.all(promises).then(() => {
      if (isUserNearBottom && container) {
        container.scrollTop = container.scrollHeight;
      }
    });
  }, [messages.length, isUserNearBottom]);

  // Синхронный скролл (оставляем ТОЛЬКО его в useLayoutEffect)
  // Без ожидания картинок — они докрутятся асинхронно
  useLayoutEffect(() => {
    if (isUserNearBottom) {
      const container = messagesContainerRef.current;
      if (container) {
        // Используем последний элемент вместо scrollHeight чтобы
        // избежать полного layout-thrashing
        const messages = container.querySelectorAll(`.${styles.chatMessage}`);
        const lastMessage = messages[messages.length - 1];
        if (lastMessage) {
          lastMessage.scrollIntoView({ block: 'end', behavior: 'instant' });
        }
      }
    }
  }, [messages.length, isUserNearBottom]);


  useEffect(() => {
    const handleClick = () => {
      if (contextMenu.visible) {
        setContextMenu(prev => ({ ...prev, visible: false }));
      }
    };
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, [contextMenu.visible]);

  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    let resizeObserver = null;

    const setupScrollLogic = () => {
      if (container._scrollData) {
        container._scrollData.hasScrolled = false;
        container.style.setProperty('--show-scroll', '1');
        return true;
      }

      const computedStyle = window.getComputedStyle(container);
      const overflowY = computedStyle.overflowY;
      
      if (overflowY === 'visible' || overflowY === 'hidden') {
        return false;
      }

      const hasVerticalScroll = container.scrollHeight > container.clientHeight;
      if (!hasVerticalScroll) {
        return false;
      }

      container.style.scrollbarGutter = 'stable';
      container.style.setProperty('--show-scroll', '1');
      
      const data = {
        hasScrolled: false,
        lastScrollTop: container.scrollTop,
        hideTimeout: null,
        isScrolling: false,
        programmaticScroll: false
      };

      container._scrollData = data;

      const handleScroll = () => {
        const currentScrollTop = container.scrollTop;
        
        if (currentScrollTop !== data.lastScrollTop) {
          if (data.programmaticScroll) {
            data.programmaticScroll = false;
            data.lastScrollTop = currentScrollTop;
            return;
          }
          
          if (!data.isScrolling) {
            container.style.setProperty('--show-scroll', '1');
            data.isScrolling = true;
          }
          
          data.hasScrolled = true;
          data.lastScrollTop = currentScrollTop;
        }
        
        if (data.hideTimeout) {
          clearTimeout(data.hideTimeout);
        }
        
        if (data.hasScrolled) {
          data.hideTimeout = setTimeout(() => {
            container.style.setProperty('--show-scroll', '0');
            data.isScrolling = false;
          }, 1000);
        }
      };

      container.addEventListener('scroll', handleScroll, { passive: true });
      data.handler = handleScroll;

      return true;
    };

    const initialized = setupScrollLogic();

    if (!initialized) {
      resizeObserver = new ResizeObserver(() => {
        if (setupScrollLogic()) {
          resizeObserver?.disconnect();
        }
      });
      resizeObserver.observe(container);
    }

    return () => {
      resizeObserver?.disconnect();
      
      const data = container._scrollData;
      if (data?.handler) {
        container.removeEventListener('scroll', data.handler);
        if (data.hideTimeout) {
          clearTimeout(data.hideTimeout);
        }
        container.style.removeProperty('--show-scroll');
        delete container._scrollData;
      }
    };
  }, []);

  const handleContextMenu = useCallback((e, name, id) => {
    e.preventDefault();
    setContextMenu({
      visible: true,
      x: e.clientX,
      y: e.clientY,
      characterName: name,
      characterId: id
    });
  }, []);

  const handleNavigate = useCallback(() => {
    if (contextMenu.characterId) {
      window.open(`/characters/${contextMenu.characterId}`, '_blank');
      setContextMenu(prev => ({ ...prev, visible: false }));
    }
  }, [contextMenu.characterId]);

  const handleSmileyClick = useCallback((smileyCode) => {
    const event = new CustomEvent('smileyClick', { detail: { smileyCode } });
    window.dispatchEvent(event);
  }, []);

  // Рендерим только последние N сообщений
  const visibleMessages = useMemo(() => {
    const limit = 500; // Максимум сообщений в DOM
    return messages.length > limit ? messages.slice(-limit) : messages;
  }, [messages]);

  return (
    <>
      <div
        className={styles.chatMessages}
        ref={messagesContainerRef}
        style={{
          fontSize: settings?.font_size ? `${settings.font_size}px` : '13px'
        }}
      >
         {visibleMessages.map((msg, index) => (
           <ChatMessage
             key={msg.id || `temp-${msg.time}-${msg.user_id}-${index}`}
             msg={msg}
             index={index}
             settings={settings}
             currentUserId={currentUserId}
             roomId={roomId}
             bellMap={bellMap}
             bellSizes={bellSizes}
             onCharacterClick={onCharacterClick}
             onContextMenu={handleContextMenu}
             onSmileyClick={handleSmileyClick}
           />
         ))}

        <div ref={messagesEndRef} />
      </div>

      {contextMenu.visible && (
        <div
          className={styles.contextMenu}
          style={{ top: contextMenu.y, left: contextMenu.x }}
        >
          <div 
            className={styles.contextMenuItem}
            onClick={handleNavigate}
          >
            <span>Инфо </span>
            <span>{contextMenu.characterName}</span>
          </div>
        </div>
      )}
    </>
  );
};

export default memo(ChatContent);