import { useState } from "react";
import {
  useListAdminCharactersQuery,
  useGetAdminCharacterQuery,
  useGetAdminInventoryQuery,
  useGetAdminCharacterResourcesQuery,
  useGiveItemMutation,
  useTakeItemMutation,
  useGiveResourceMutation,
  useTakeResourceMutation,
  useAddMoneyMutation,
  useSetMoneyMutation,
} from "../../../../entities/admin/api";
import CharacterModal from "./CharacterModal";
import styles from "../../AdminPage.module.css";

export default function AdminCharactersTab() {
  const [search, setSearch] = useState("");
  const [searchTrigger, setSearchTrigger] = useState("");
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const { data: charactersResult, isLoading: charsLoading } = useListAdminCharactersQuery(
    { search: searchTrigger.trim() || undefined, limit: 50 },
    { skip: !searchTrigger }
  );
  const characters = charactersResult?.objects || [];

  const { data: details } = useGetAdminCharacterQuery(selected?.id, { skip: !selected?.id });
  const { data: inventory } = useGetAdminInventoryQuery(selected?.id, { skip: !selected?.id });
  const { data: resources = [] } = useGetAdminCharacterResourcesQuery(selected?.id, { skip: !selected?.id });

  const [giveItem] = useGiveItemMutation();
  const [takeItem] = useTakeItemMutation();
  const [giveResource] = useGiveResourceMutation();
  const [takeResource] = useTakeResourceMutation();
  const [addMoney] = useAddMoneyMutation();
  const [setMoney] = useSetMoneyMutation();

  const openCharacter = (character) => {
    setSelected(character);
    setError("");
    setSuccess("");
  };

  const reportMutation = async (operation) => {
    setError("");
    setSuccess("");
    try {
      const result = await operation();
      if (result?.rejected) {
        const rejected = result.rejected.map(({ currency, error: requestError }) =>
          `${currency}: ${requestError?.data?.detail || "операция не выполнена"}`
        );
        if (result.fulfilled.length) setSuccess(`Применено: ${result.fulfilled.map(({ currency }) => currency).join(", ")}`);
        setError(rejected.join("; "));
      } else {
        setSuccess("Операция выполнена");
      }
    } catch (e) {
      setError(e?.data?.detail || "Ошибка выполнения операции");
    }
  };

  return (
    <div>
      <div className={styles.filters}>
        <input value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === "Enter" && setSearchTrigger(search)} placeholder="Имя персонажа" />
        <button onClick={() => setSearchTrigger(search)} disabled={charsLoading}>Найти</button>
      </div>
      {error && <div className={styles.error}>{error}</div>}
      {success && <div className={styles.success}>{success}</div>}
      <table className={styles.table}>
        <thead><tr><th>Имя</th><th>Уровень</th><th>Локация</th><th>Онлайн</th><th /></tr></thead>
        <tbody>{characters.map((character) => <tr key={character.id}><td>{character.name}</td><td>{character.level}</td><td>{character.location_slug || "—"}</td><td>{character.is_online ? "Да" : "Нет"}</td><td><button onClick={() => openCharacter(character)}>Открыть</button></td></tr>)}</tbody>
      </table>
      {!charsLoading && characters.length === 0 && <div className={styles.empty}>Введите имя и выполните поиск</div>}
      {selected && (
        <CharacterModal
          character={details || selected}
          inventory={inventory}
          resources={resources}
          onClose={() => setSelected(null)}
          onMutation={reportMutation}
          giveItem={(data) => giveItem({ characterId: selected.id, data }).unwrap()}
          takeItem={(data) => takeItem({ characterId: selected.id, data }).unwrap()}
          giveResource={(data) => giveResource({ characterId: selected.id, data }).unwrap()}
          takeResource={(data) => takeResource({ characterId: selected.id, data }).unwrap()}
          addMoney={(amounts, reason) => addMoney({ characterId: selected.id, amounts, reason })}
          setMoney={(amounts, reason) => setMoney({ characterId: selected.id, amounts, reason })}
        />
      )}
    </div>
  );
}