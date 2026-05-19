import { createApp } from "vue";
import { createPinia } from "pinia";

import App from "./App.vue";
import "./style.css";
import "./styles/cards-forms.css";
import "./styles/ui-shared.css";
import "./styles/workspace.css";

const app = createApp(App);

app.config.errorHandler = (error, instance, info) => {
  console.error("[前端异常] Vue 组件执行失败", {
    error: error instanceof Error ? error.message : String(error),
    stack: error instanceof Error ? error.stack : undefined,
    component: instance?.$options.name,
    info,
  });
};

window.addEventListener("unhandledrejection", (event) => {
  console.error("[前端异常] Promise 未处理失败", {
    reason: event.reason instanceof Error ? event.reason.message : String(event.reason),
    stack: event.reason instanceof Error ? event.reason.stack : undefined,
  });
});

window.addEventListener("error", (event) => {
  console.error("[前端异常] 浏览器运行错误", {
    message: event.message,
    source: event.filename,
    line: event.lineno,
    column: event.colno,
    error: event.error instanceof Error ? event.error.message : String(event.error),
  });
});

app.use(createPinia());
app.mount("#app");
