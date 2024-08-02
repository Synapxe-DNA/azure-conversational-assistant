export enum ProfileType {
  Myself = "MYSELF",
  Others = "OTHERS",
  General = "GENERAL",
  Undefined = "",
}

export enum ProfileGender {
  Male = "MALE",
  Female = "FEMALE",
  Undefined = "",
}

export interface Profile {
  id: string;
  name: string;
  profile_type: ProfileType;
  gender: ProfileGender;
  age: number;
  existing_conditions: string;
}

export const GeneralProfile: Profile = {
  id: "",
  name: "General",
  profile_type: ProfileType.General,
  gender: ProfileGender.Undefined,
  age: NaN,
  existing_conditions: "",
};
