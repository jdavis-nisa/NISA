import axios from "axios"

export const NISA_API_KEY = "d551fd7e05134c52b84286c201f0f36d8ddeb5e0611ed771ba44d6a4264f39cf"

const api = axios.create({
  headers: {
    "X-NISA-API-Key": NISA_API_KEY,
  },
})

export default api
