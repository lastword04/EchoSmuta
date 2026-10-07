import { Outlet } from 'react-router-dom';
import { Sky } from '../../shared/ui/Sky/Sky';
import styles from './MainLayout.module.css';

export const MainLayout = () => (
  <div className={styles.layout}>
    <div className={styles.skyHolder}>
      <Sky />
    </div>
    <div className={styles.content}>
      <Outlet />
    </div>
  </div>
);