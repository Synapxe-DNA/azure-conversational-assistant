import { MigrationFactory } from "../../types/configs/ngx.type"

export function NgxIndexedDbMigrationFactory(): MigrationFactory {
  return {
    1: (db, transaction) => {
      const messagesStore = transaction.objectStore("messages")
      messagesStore.createIndex("role", "role", { unique: false })
      messagesStore.createIndex("timestamp", "timestamp", { unique: false })
    },
  }
}
