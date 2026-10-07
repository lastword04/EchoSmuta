import React from 'react';
import styles from './SquarePattern.module.css';

const SquarePattern = ({ 
  squares = [], 
  className = '',
  squareClassName = '',
  containerStyle = {},
  squareSize = 27 // Новый пропс для размера квадратиков
}) => {
  return (
    <div 
      className={`${styles.squarePattern} ${className}`}
      style={containerStyle}
    >
      {squares.map((square, index) => (
        <div
          key={index}
          className={`${styles.square} ${square.className ? styles[square.className] : ''} ${squareClassName}`}
          style={{
            ...square.style,
            width: `${squareSize}px`,
            height: `${squareSize}px`,
            minWidth: `${squareSize}px`,
            minHeight: `${squareSize}px`
          }}
        >
          {square.content && (
            typeof square.content === 'string' ? (
              square.content.startsWith('http') || square.content.startsWith('/') ? (
                <img 
                  src={square.content} 
                  alt={square.alt || `Square ${index}`}
                  className={styles.squareImage}
                />
              ) : (
                <span className={styles.squareText}>{square.content}</span>
              )
            ) : (
              square.content
            )
          )}
        </div>
      ))}
    </div>
  );
};

export default SquarePattern;