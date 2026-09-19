export type User = {
  id: string;
  email: string;
  full_name: string;
  status: string;
};

export type LoginPayload = {
  email: string;
  password: string;
};

export type RegisterPayload = LoginPayload & {
  full_name: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};
