import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

// fonts are bundled with the app, so it looks the same with or without internet
import "@fontsource/barlow-condensed/600.css";
import "@fontsource/barlow-condensed/700.css";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
import "@fontsource/noto-sans-sinhala/400.css";
import "@fontsource/noto-sans-sinhala/600.css";
import "@fontsource/noto-sans-sinhala/700.css";
import "./styles/tokens.css";
import "./styles/global.css";

import { App } from "./App";
import { I18nProvider } from "./i18n/I18nProvider";
import { CheckProvider } from "./state/CheckContext";
import { MetaProvider } from "./state/MetaContext";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <I18nProvider>
        <MetaProvider>
          <CheckProvider>
            <App />
          </CheckProvider>
        </MetaProvider>
      </I18nProvider>
    </BrowserRouter>
  </StrictMode>,
);
