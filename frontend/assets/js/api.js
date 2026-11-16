// FoodieExpress API Service

const API = {
    setTokens(data) {
        if (data.access_token) {
            sessionStorage.setItem(
                FOODIE_CONFIG.TOKEN_KEYS.ACCESS,
                data.access_token
            );
        }

        if (data.refresh_token) {
            sessionStorage.setItem(
                FOODIE_CONFIG.TOKEN_KEYS.REFRESH,
                data.refresh_token
            );
        }
    },

    getAccessToken() {
        return sessionStorage.getItem(
            FOODIE_CONFIG.TOKEN_KEYS.ACCESS
        );
    },

    getRefreshToken() {
        return sessionStorage.getItem(
            FOODIE_CONFIG.TOKEN_KEYS.REFRESH
        );
    },

    clearTokens() {
        sessionStorage.removeItem(
            FOODIE_CONFIG.TOKEN_KEYS.ACCESS
        );
        sessionStorage.removeItem(
            FOODIE_CONFIG.TOKEN_KEYS.REFRESH
        );
    },

    async request(endpoint, options = {}) {
        const headers = { ...(options.headers || {}) };
        const token = this.getAccessToken();

        if (token) {
            headers.Authorization = `Bearer ${token}`;
        }

        let body = options.body;

        if (
            body &&
            !(body instanceof FormData) &&
            typeof body !== "string"
        ) {
            headers["Content-Type"] = "application/json";
            body = JSON.stringify(body);
        }

        headers.Accept = "application/json";

        try {
            const response = await fetch(
                `${FOODIE_CONFIG.API_BASE_URL}${endpoint}`,
                {
                    ...options,
                    headers,
                    body
                }
            );

            const contentType =
                response.headers.get("content-type") || "";

            const result = contentType.includes("application/json")
                ? await response.json()
                : await response.text();

            if (!response.ok) {
                const message =
                    typeof result === "object"
                        ? result.detail || result.message
                        : result;

                throw new Error(
                    message || `Request failed: ${response.status}`
                );
            }

            return result;

        } catch (error) {
            console.error(
                "FoodieExpress API Error:",
                error.message
            );
            throw error;
        }
    },

    get(endpoint) {
        return this.request(endpoint, { method: "GET" });
    },

    post(endpoint, data) {
        return this.request(endpoint, {
            method: "POST",
            body: data
        });
    },

    put(endpoint, data) {
        return this.request(endpoint, {
            method: "PUT",
            body: data
        });
    },

    patch(endpoint, data) {
        return this.request(endpoint, {
            method: "PATCH",
            body: data
        });
    },

    delete(endpoint) {
        return this.request(endpoint, { method: "DELETE" });
    }
};

window.API = API;
