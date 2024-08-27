export enum ApiProfileType {
  General = "general",
  Myself = "myself",
  Others = "others"
}

export enum ApiProfileGender {
  Male = "male",
  Female = "female"
}

export interface ApiProfile {
  profile_type: "general" | "myself" | "others";
  user_age: number;
  user_gender: "male" | "female";
  user_condition: string;
}
