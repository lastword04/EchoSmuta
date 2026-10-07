import styles from "../AdminPage.module.css";

export default function MutationSection({ title, children }) {
  return (
    <section className={styles.mutationSection}>
      <h4>{title}</h4>
      {children}
    </section>
  );
}