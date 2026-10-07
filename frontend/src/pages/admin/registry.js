import EconomyTab from "./domains/economy/EconomyTab";
import JournalTab from "./domains/economy/JournalTab";
import StatisticsTab from "./domains/economy/StatisticsTab";

import CharactersTab from "./domains/characters/CharactersTab";
import AdminCharactersTab from "./domains/characters/AdminCharactersTab";

import ItemsCatalogTab from "./domains/inventory/ItemsCatalogTab";
import ResourcesCatalogTab from "./domains/inventory/ResourcesCatalogTab";
import AdminHistoryTab from "./domains/inventory/AdminHistoryTab";
import LedgerTab from "./domains/inventory/LedgerTab";

import AuthLogsTab from "./domains/security/AuthLogsTab";

export const ADMIN_TABS = [
  { group: "Скупочный магазин", items: [
    { id: "economy",    label: "Таблица",    component: EconomyTab },
    { id: "journal",    label: "Журнал",     component: JournalTab },
    { id: "statistics", label: "Статистика", component: StatisticsTab },    
  ]},
  { group: "Персонажи", items: [
    { id: "adminCharacters", label: "Персонажи",       component: AdminCharactersTab },
    { id: "characters",      label: "Аккаунты и баны", component: CharactersTab },    
  ]},
  { group: "Майнинг", items: [
    { id: "items",          label: "Предметы", component: ItemsCatalogTab },
    { id: "resources",      label: "Ресурсы",  component: ResourcesCatalogTab },
    { id: "adminHistory",   label: "История",  component: AdminHistoryTab },    
    { id: "ledger", label: "Ledger", component: LedgerTab },
  ]},  
  { group: "Безопасность", items: [
    { id: "authLogs", label: "Логи входов", component: AuthLogsTab },
  ]},
];