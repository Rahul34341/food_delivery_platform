const FOODIE_CONFIG = {
    APP_NAME: "FoodieExpress",

    API_BASE_URL: "http://127.0.0.1:8000",

    ENDPOINTS: {
        REGISTER: "/auth/register",
        LOGIN: "/auth/login",
        LOGOUT: "/auth/logout",
        REFRESH: "/auth/refresh",
        FORGOT_PASSWORD: "/auth/password-reset/request",
        RESET_PASSWORD: "/auth/password-reset/confirm",
        CHANGE_PASSWORD: "/auth/change-password",
        PROFILE: "/auth/me",

        RESTAURANTS: "/restaurants/",
        MY_RESTAURANTS: "/restaurants/my-restaurants"
    },

    TOKEN_KEYS: {
        ACCESS: "foodie_access_token",
        REFRESH: "foodie_refresh_token"
    }
};

// Make configuration available to other JavaScript files.
window.FOODIE_CONFIG = FOODIE_CONFIG;
