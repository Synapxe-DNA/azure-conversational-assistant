import { VersionedSchema } from "../../types/configs/ngx.type"

export const NgxIndexedDbSchema: VersionedSchema = {
  version_1: [
    {
      store: "profiles",
      storeConfig: { keyPath: "id", autoIncrement: false },
      storeSchema: [
        { name: "name", keypath: "name", options: { unique: false } },
        { name: "profile_type", keypath: "profile_type", options: {unique: false} },
        { name: "age", keypath: "age", options: { unique: false } },
        { name: "gender", keypath: "gender", options: { unique: false } },
        {
          name: "existing_conditions",
          keypath: "existing_conditions",
          options: { unique: false },
        },
      ],
    },
    {
      store: "messages",
      storeConfig: { keyPath: "id", autoIncrement: false },
      storeSchema: [
        {
          name: "profile_id",
          keypath: "profile_id",
          options: { unique: false },
        },
        { name: "role", keypath: "role", options: { unique: false } },
        { name: "message", keypath: "message", options: { unique: false } },
        { name: "timestamp", keypath: "timestamp", options: { unique: false } },
        { name: "sources", keypath: "sources", options: { unique: false } },
      ],
    },
  ],
}
