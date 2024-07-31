import { ObjectStoreMeta, ObjectStoreSchema } from "ngx-indexed-db"

export interface VersionedSchema {
  [key: string]: ObjectStoreMeta[]
}

export interface MigrationFactory {
  [key: number]: (db: IDBDatabase, transaction: IDBTransaction) => void
}
