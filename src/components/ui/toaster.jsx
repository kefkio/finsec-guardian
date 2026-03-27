import { useToast } from "@/hooks/use-toast";
import { Toast, ToastClose, ToastDescription, ToastProvider, ToastTitle, ToastViewport } from "@/components/ui/toast";
import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function Toaster() {
  const {
    toasts
  } = useToast();
  return /*#__PURE__*/_jsxs(ToastProvider, {
    children: [toasts.map(function ({
      id,
      title,
      description,
      action,
      ...props
    }) {
      return /*#__PURE__*/_jsxs(Toast, {
        ...props,
        children: [/*#__PURE__*/_jsxs("div", {
          className: "grid gap-1",
          children: [title && /*#__PURE__*/_jsx(ToastTitle, {
            children: title
          }), description && /*#__PURE__*/_jsx(ToastDescription, {
            children: description
          })]
        }), action, /*#__PURE__*/_jsx(ToastClose, {})]
      }, id);
    }), /*#__PURE__*/_jsx(ToastViewport, {})]
  });
}