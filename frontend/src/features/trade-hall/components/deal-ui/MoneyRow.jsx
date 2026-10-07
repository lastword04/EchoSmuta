import btn from "../../../../shared/styles/buttons.module.css";

export function MoneyRow({ currency, amount, isEditable, isProcessing, onRemove }) {
  const label = currency === 'ducats' ? 'дт' : 'злт';
  
  return (
    <tr>
      <td>Деньги {Number(amount).toFixed(2)} {label}.</td>
      {isEditable && (
        <td>
          <button 
            className={`${btn.gameButton} ${btn.sizeSmall}`} 
            onClick={onRemove} 
            disabled={isProcessing}
          >
            Забрать
          </button>
        </td>
      )}
    </tr>
  );
}