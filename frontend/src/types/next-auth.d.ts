import "next-auth"
import "next-auth/jwt"

declare module "next-auth" {
  interface Session {
    accessToken: string
    user: {
      id: string
      email: string
      plan: string
    }
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken: string
    plan: string
  }
}
