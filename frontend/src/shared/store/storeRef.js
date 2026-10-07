// Тонкая обёртка над синглтоном Redux-store.
//
// Сборка хранилища (configureStore, rootReducer, middleware) живёт в
// app/providers/store/index.js — слой app. Нижние слои (shared/hooks, pages,
// features) не имеют права импортировать app напрямую, но некоторым из них
// нужен императивный доступ к состоянию (store.getState()) вне React-хуков.
// Для этого app/providers/store/index.js заполняет storeRef.current при
// создании хранилища, а потребители читают storeRef.current.getState().
//
// К моменту любого пользовательского взаимодействия store уже создан
// (это происходит на импорте app/index.jsx раньше монтирования дерева).
export const storeRef = { current: null };
