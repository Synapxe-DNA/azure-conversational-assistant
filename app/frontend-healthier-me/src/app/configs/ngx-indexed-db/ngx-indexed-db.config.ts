import { DBConfig } from "ngx-indexed-db";
import { NgxIndexedDbSchema } from "./schema.config";
import { NgxIndexedDbMigrationFactory } from "./migration-factory.config";

export const NgxIndexedDbConfig: DBConfig = {
  name: "HealthierME",
  version: 1,
  objectStoresMeta: NgxIndexedDbSchema["version_1"],
  migrationFactory,
};

export function migrationFactory() {
  return {
    1: (db: any, transaction: any) => {
      const messagesStore = transaction.objectStore("messages");
      messagesStore.createIndex("role", "role", { unique: false });
      messagesStore.createIndex("timestamp", "timestamp", { unique: false });
    },
  };
}
