import { useState } from "react";
import { useSearchCharactersQuery } from "../../../entities/admin/api";
import styles from "../AdminPage.module.css";

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export default function CharacterPicker({ onSelect, placeholder = "Ник или ID персонажа" }) {
  const [query, setQuery] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [searched, setSearched] = useState(false);

  const { data: searchResult } = useSearchCharactersQuery(
    { name_like: searchTerm },
    { skip: !searchTerm }
  );

  const search = () => {
    const q = query.trim();
    if (!q) return;
    if (UUID_RE.test(q)) {
      onSelect(q, q);
      setQuery("");
      return;
    }
    setSearchTerm(q);
    setSearched(true);
  };

  const results = searchResult?.objects || [];

  return (
    <div className={styles.picker}>
      <input
        type="text"
        placeholder={placeholder}
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setSearched(false);
        }}
        onKeyDown={(e) => e.key === "Enter" && search()}
      />
      <button type="button" onClick={search}>🔍</button>
      {searched && (
        <div className={styles.pickerDropdown}>
          {results.length === 0 ? (
            <div className={styles.pickerItem}>Ничего не найдено</div>
          ) : (
            results.map((c) => (
              <div
                key={c.id}
                className={styles.pickerItem}
                onClick={() => {
                  onSelect(c.id, c.name);
                  setQuery("");
                  setSearchTerm("");
                  setSearched(false);
                }}
              >
                {c.name}{" "}
                <span className={styles.pickerId}>({c.id.substring(0, 8)}...)</span>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}