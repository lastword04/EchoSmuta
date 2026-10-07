import btn from "../../../../shared/styles/buttons.module.css";

export function AssetRow({
  item,
  isEditable,
  isProcessing,
  onItemClick,
  onResourceClick,
  onRemoveItem,
  onRemoveResource,
  displayName,
  isItemAsset,
}) {
  const isResource = item.asset_type === "RESOURCE";
  const isItem = isItemAsset(item);

  // Неизвестный asset_type (не RESOURCE и не ITEM/INVENTORY_ITEM):
  // не рендерим строку вообще — иначе handleClick ничего бы не сделал,
  // а handleRemove вызвал бы неверный обработчик удаления.
  if (!isResource && !isItem) return null;
  
  const handleClick = () => {
    if (isItem) onItemClick(item);
    else if (isResource) onResourceClick(item.resource_slug);
  };
  
  const handleRemove = () => {
    if (isResource) return onRemoveResource(item.resource_slug)();
    return onRemoveItem(item.id)();
  };

  return (
    <tr>
      <td>
        <span className={btn.clickableItemName} onClick={handleClick}>
          {displayName(item)}
        </span>
        {item.amount > 1 ? ` ${item.amount} шт.` : ""}
      </td>
      {isEditable && (
        <td>
          <button 
            className={`${btn.gameButton} ${btn.sizeSmall}`} 
            onClick={handleRemove} 
            disabled={isProcessing}
          >
            Забрать
          </button>
        </td>
      )}
    </tr>
  );
}