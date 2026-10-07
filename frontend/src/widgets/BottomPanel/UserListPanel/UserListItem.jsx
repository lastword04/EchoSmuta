import { getRaceShield, getRaceDisplayName, getGenderDisplayName } from '../../../entities/character/config/race';
import { useAutoFontSize } from '../../../shared/hooks/ui/useAutoFontSize';
import { useMediaQuery } from '../../../shared/hooks/ui/useMediaQuery';
import styles from './UserListPanel.module.css';

export const UserListItem = ({ 
    user,     
    isLastItem, 
    observerCallback, 
    character_id, 
    showTitles,
    onToggleIgnore,
    onPrivateClick,
    onUserLinkClick,
    onNavigate,
    isIgnorePending = false,
}) => {
    const isMobile = useMediaQuery('(max-width: 768px)');
    const maxNameWidth = isMobile ? window.innerWidth - 100 : 190;
    const nameRef = useAutoFontSize(maxNameWidth, 13, 5);

    const shieldIcon = getRaceShield(user.race, user.is_male);
    const ignoreTitle = showTitles
        ? (user.is_ignored
            ? `Снять игнор с персонажа ${user.name}`
            : `Игнор персонажа ${user.name}`)
        : undefined;

    const isSelf = user.id === character_id;

    const checkboxSrc = user.is_ignored
        ? '/images/widgets/userlist-panel/checkbox_active.jpg'
        : '/images/widgets/userlist-panel/checkbox_not_active.png';

    return (
        <div
            className={styles.userListItem}
            ref={isLastItem ? observerCallback : null}
        >
            {/* Игнор */}
            {isSelf ? (
                <div className={styles.hiddenSpacer}></div>
            ) : (
                <img
                    src={checkboxSrc}
                    alt={user.is_ignored ? 'Игнорируется' : 'Не игнорируется'}
                    className={styles.checkboxImg}
                    title={ignoreTitle}
                    onClick={() => {
                        if (!isIgnorePending) onToggleIgnore(user);
                    }}
                    style={{
                        cursor: 'pointer',                        
                    }}
                />
            )}

            <div className={styles.spacer} title="Вне клана"></div>

            {/* Приват */}
                <img
                    src="/images/widgets/userlist-panel/private.gif"
                    alt="Приват"
                    className={styles.privateIcon}
                    title={showTitles ? `Приватное сообщение` : undefined}
                    onClick={() => onPrivateClick(user)}
                />

            {/* Имя пользователя */}
            <span
                className={styles.userLink}
                ref={nameRef}
                title={showTitles ?  `Сообщение` : undefined}
                onClick={() => onUserLinkClick(user)}
                style={{
                    cursor: 'pointer',
                    pointerEvents: 'auto',
                }}
            >
                {user.name}
            </span>

            {/* Уровень */}
            <strong
                className={styles.userLevel}
                onClick={() => onNavigate(user.id)}
                title={
                    showTitles
                        ? `Информация о персонаже ${user.name}`
                        : undefined
                }
                style={{
                    cursor: 'pointer',
                    pointerEvents: 'auto',
                    opacity: 1,
                }}
            >
                [{user.level}]
            </strong>

            {/* Щит (раса/пол) */}
            {shieldIcon && (
                <img
                    src={shieldIcon}
                    alt={`${getRaceDisplayName(user.race)} ${getGenderDisplayName(user.is_male)}`}
                    className={styles.shieldIcon}
                    title={
                        showTitles
                            ? `Информация о персонаже ${user.name}`
                            : undefined
                    }
                    onClick={() => onNavigate(user.id)}
                    style={{
                        cursor: 'pointer',
                        pointerEvents: 'auto',
                        opacity: 1,
                    }}
                    onError={(e) => {
                        e.target.style.display = 'none';
                    }}
                />
            )}
            <div className={styles.additionalIcon}></div>
        </div>
    );
};
