import { useState } from "react";
import MutationSection from "../../shared/MutationSection";
import styles from "../../AdminPage.module.css";

export default function CharacterModal({ character, inventory, resources, onClose, onMutation, giveItem, takeItem, giveResource, takeResource, addMoney, setMoney }) {
  const [giveItemState, setGiveItem] = useState({ item_slug: "", amount: "" });
  const [takeItemState, setTakeItem] = useState({ inventory_item_id: "", item_slug: "", amount: "", force: false });
  const [resource, setResource] = useState({ resource_slug: "", amount: "" });
  const [money, setMoneyState] = useState({ ducats: "", gold: "" });
  const [reason, setReason] = useState(""); // ← Новое состояние для причины
  const [showInventory, setShowInventory] = useState(false);
  const [showResources, setShowResources] = useState(false);
  const [loading, setLoading] = useState(false);
  
  const groups = inventory ? [["Инвентарь", inventory.inventory], ["Лавка", inventory.shop], ["Продажа", inventory.sale], ["Сделки", inventory.deals]] : [];
  const inventoryCount = groups.reduce((total, [, items]) => total + (items?.length || 0), 0);
  const validAmount = (value) => Number(value) > 0;

  return (
    <div className={styles.modalBackdrop} role="dialog" aria-modal="true">
      <div className={styles.modal}>
        <button className={styles.modalClose} onClick={onClose}>×</button>
        <h2>{character.name}</h2>
        <div className={styles.detailRow}>ID: <code className={styles.code}>{character.id}</code></div>
        <div className={styles.detailRow}>Уровень: {character.level}; локация: {character.location_slug || "—"}</div>
        <div className={styles.detailRow}>Дукаты: {character.ducats}; золото: {character.gold}</div>

        {/* ← Новое поле причины */}
        <div style={{ marginBottom: 16, marginTop: 16 }}>
          <label style={{ display: 'block', marginBottom: 4, fontSize: 14, fontWeight: 600 }}>
            Причина операции (необязательно)
          </label>
          <input
            type="text"
            placeholder="Например: компенсация за баг, ручная корректировка"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc', boxSizing: 'border-box' }}
          />
        </div>

        <div className={styles.mutationGrid}>
          <MutationSection title="Выдать предмет">
            <input placeholder="item_slug" value={giveItemState.item_slug} onChange={(e) => setGiveItem({ ...giveItemState, item_slug: e.target.value })} />
            <input type="number" min="1" placeholder="Количество" value={giveItemState.amount} onChange={(e) => setGiveItem({ ...giveItemState, amount: e.target.value })} />
            <button disabled={loading || !giveItemState.item_slug || !validAmount(giveItemState.amount)} onClick={async () => { setLoading(true); try { await onMutation(() => giveItem({ item_slug: giveItemState.item_slug, amount: Number(giveItemState.amount), reason: reason || undefined })); } finally { setLoading(false); } }}>Выдать</button>
          </MutationSection>
          
          <MutationSection title="Забрать предмет">
            <input placeholder="inventory_item_id (или slug)" value={takeItemState.inventory_item_id} onChange={(e) => setTakeItem({ ...takeItemState, inventory_item_id: e.target.value, item_slug: "" })} />
            <input placeholder="item_slug (или ID)" value={takeItemState.item_slug} onChange={(e) => setTakeItem({ ...takeItemState, item_slug: e.target.value, inventory_item_id: "" })} />
            <input type="number" min="1" placeholder="Количество" value={takeItemState.amount} onChange={(e) => setTakeItem({ ...takeItemState, amount: e.target.value })} />
            <label className={styles.checkboxLabel}><input type="checkbox" checked={takeItemState.force} onChange={(e) => setTakeItem({ ...takeItemState, force: e.target.checked })} />Принудительно снять экипировку</label>
            <button disabled={loading || !(takeItemState.inventory_item_id || takeItemState.item_slug) || !validAmount(takeItemState.amount)} onClick={async () => { setLoading(true); try { await onMutation(() => takeItem({ ...(takeItemState.inventory_item_id ? { inventory_item_id: takeItemState.inventory_item_id } : { item_slug: takeItemState.item_slug }), amount: Number(takeItemState.amount), force: takeItemState.force, reason: reason || undefined })); } finally { setLoading(false); } }}>Забрать</button>
          </MutationSection>
          
          <MutationSection title="Ресурс">
            <input placeholder="resource_slug" value={resource.resource_slug} onChange={(e) => setResource({ ...resource, resource_slug: e.target.value })} />
            <input type="number" min="1" placeholder="Количество" value={resource.amount} onChange={(e) => setResource({ ...resource, amount: e.target.value })} />
            <button disabled={loading || !resource.resource_slug || !validAmount(resource.amount)} onClick={async () => { setLoading(true); try { await onMutation(() => giveResource({ resource_slug: resource.resource_slug, amount: Number(resource.amount), reason: reason || undefined })); } finally { setLoading(false); } }}>Выдать</button>
            <button disabled={loading || !resource.resource_slug || !validAmount(resource.amount)} onClick={async () => { setLoading(true); try { await onMutation(() => takeResource({ resource_slug: resource.resource_slug, amount: Number(resource.amount), reason: reason || undefined })); } finally { setLoading(false); } }}>Забрать</button>
          </MutationSection>
          
          <MutationSection title="Деньги">
            <input type="number" min="0" placeholder="Дукаты" value={money.ducats} onChange={(e) => setMoneyState({ ...money, ducats: e.target.value })} />
            <input type="number" min="0" placeholder="Золото" value={money.gold} onChange={(e) => setMoneyState({ ...money, gold: e.target.value })} />
            <button disabled={loading || (money.ducats === "" && money.gold === "")} onClick={async () => { setLoading(true); try { await onMutation(() => addMoney(money, reason)); } finally { setLoading(false); } }}>Добавить</button>
            <button disabled={loading || (money.ducats === "" && money.gold === "")} onClick={async () => { setLoading(true); try { await onMutation(() => setMoney(money, reason)); } finally { setLoading(false); } }}>Установить</button>
          </MutationSection>
        </div>

        <h3>Ресурсы</h3>
        <button className={styles.inventoryToggle} onClick={() => setShowResources(!showResources)}>
          {showResources ? "Скрыть ресурсы" : `Показать ресурсы (${resources.length})`}
        </button>
        {showResources && <table className={styles.table}><thead><tr><th>Название</th><th>Slug</th><th>Категория</th><th>Количество</th></tr></thead><tbody>{resources.map((item) => <tr key={item.resource_slug}><td>{item.resource_name}</td><td>{item.resource_slug}</td><td>{item.category || "—"}</td><td>{item.amount}</td></tr>)}</tbody></table>}

        <h3>Инвентарь</h3>
        <button className={styles.inventoryToggle} onClick={() => setShowInventory(!showInventory)}>
          {showInventory ? "Скрыть инвентарь" : `Показать инвентарь (${inventoryCount} предметов)`}
        </button>
        {showInventory && groups.map(([title, items]) => <div key={title} className={styles.inventoryGroup}><h4>{title}</h4>{items?.length ? <table className={styles.table}><thead><tr><th>Предмет</th><th>Slug</th><th>Кол-во</th><th>Состояние</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td>{item.item_name}</td><td>{item.item_slug}</td><td>{item.amount}</td><td>{item.is_equipped && "Экипирован "}{item.is_expired && "Просрочен"}{!item.is_equipped && !item.is_expired && "—"}</td></tr>)}</tbody></table> : <div className={styles.empty}>Пусто</div>}</div>)}
      </div>
    </div>
  );
}