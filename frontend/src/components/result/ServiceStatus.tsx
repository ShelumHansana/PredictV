import type { DiagnosisResult, Meta, ServiceState } from "../../api/types";
import { useI18n } from "../../i18n/I18nProvider";
import { Badge } from "../ui/Badge";
import { Panel } from "../ui/Panel";
import "./result.css";

const tone: Record<ServiceState, "pass" | "warn" | "fail" | undefined> = { recent: "pass", due: "warn", overdue: "fail", unknown: undefined };

export function ServiceStatus({ service, meta }: { service: DiagnosisResult["service"]; meta: Meta }) {
  const { t, pick } = useI18n();
  return (
    <Panel title={t("svc_h")}>
      {meta.service_items.map(item => (
        <div className="row" key={item.id}>
          <b>{pick(item)}</b>
          <Badge tone={tone[service[item.id]]}>{t(`st_${service[item.id]}`)}</Badge>
        </div>
      ))}
    </Panel>
  );
}
