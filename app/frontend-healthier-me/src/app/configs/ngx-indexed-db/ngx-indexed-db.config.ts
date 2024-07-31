import { DBConfig } from "ngx-indexed-db"
import { NgxIndexedDbSchema } from "./schema.config"

export const NgxIndexedDbConfig: DBConfig = {
  name: "HealthierME",
  version: 1,
  objectStoresMeta: NgxIndexedDbSchema["version_1"],
}
