// Type declarations for components/ui/Toast.js
//
// Without these, TypeScript infers useToast() as returning `never` (because
// ToastContext = createContext(null) widens to React.Context<null> and the
// `if (!context) throw` in useToast narrows past null). TSX consumers then
// get "Type 'never' has no call signatures" on addToast.

import type { ReactNode } from "react";

export type ToastType = "success" | "error" | "warning" | "info";

export interface ToastApi {
  addToast: (message: string, type?: ToastType) => void;
}

export function ToastProvider(props: { children: ReactNode }): JSX.Element;

export function useToast(): ToastApi;
