import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { useGetCurrencyOperationsQuery } from "../../entities/admin/api";
import { setUserRole } from "../../shared/store/userRoleSlice";
import { Spinner } from "../../shared/ui/Spinner/Spinner";
import { ADMIN_TABS } from "./registry";
import styles from "./AdminPage.module.css";

function AdminPage() {
  const dispatch = useDispatch();
  const userRole = useSelector((state) => state.local?.userRole);
  const [activeTab, setActiveTab] = useState("ledger");
  const [probeDone, setProbeDone] = useState(false);

  const isAdmin = (userRole ?? "").toLowerCase() === "admin";

  const { data: probeData, error: probeError } = useGetCurrencyOperationsQuery(
    {},
    { skip: userRole !== null }
  );

  useEffect(() => {
    if (userRole !== null) return;
    if (probeData !== undefined) {
      dispatch(setUserRole("admin"));
      setProbeDone(true);
    } else if (probeError?.status) {
      const status = probeError.status;
      if (status === 401) return;
      if (status === 403) {
        dispatch(setUserRole("user"));
        setProbeDone(true);
        return;
      }
      setProbeDone(true);
    }
  }, [userRole, probeData, probeError?.status, dispatch]);

  if (userRole !== null && !isAdmin) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ authRequired: "Недостаточно прав для админ-панели." }}
      />
    );
  }

  if (userRole === null && !probeDone) {
    return (
      <div
        className={styles.wrapper}
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "60vh",
        }}
      >
        <Spinner />
      </div>
    );
  }

  const ActiveComponent = ADMIN_TABS
    .flatMap((group) => group.items)
    .find((tab) => tab.id === activeTab)?.component;

  return (
    <div className={styles.wrapper}>
      <div className={styles.tabs}>
        {ADMIN_TABS.map((group) => (
          <div key={group.group} style={{ marginBottom: 8 }}>
            <div style={{ fontSize: 11, color: "#888", marginBottom: 4, paddingLeft: 8 }}>
              {group.group}
            </div>
            {group.items.map((tab) => (
              <button
                key={tab.id}
                className={`${styles.tab} ${activeTab === tab.id ? styles.active : ""}`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>
        ))}
      </div>

      <div className={styles.content}>
        {ActiveComponent ? (
          <ActiveComponent />
        ) : (
          <div style={{ padding: 20, color: "#888" }}>Выберите раздел</div>
        )}
      </div>
    </div>
  );
}

export default AdminPage;