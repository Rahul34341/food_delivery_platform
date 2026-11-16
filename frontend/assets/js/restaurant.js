// FoodieExpress Restaurant Management

function showRestaurantMessage(message, type, elementId = "restaurantMessage") {
    const element = document.getElementById(elementId);

    if (!element) return;

    element.textContent = message;
    element.className = `message ${type}`;
}

// ---------------- RESTAURANT REGISTRATION ----------------

const restaurantForm = document.getElementById("restaurantForm");

if (restaurantForm) {
    restaurantForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const restaurantData = {
            name: document.getElementById("name").value.trim(),
            description: document.getElementById("description").value.trim() || null,
            address: document.getElementById("address").value.trim(),
            city: document.getElementById("city").value.trim(),
            phone: document.getElementById("phone").value.trim() || null
        };

        const button = restaurantForm.querySelector("button[type='submit']");
        button.disabled = true;
        button.textContent = "Registering...";

        try {
            const response = await API.post(
                FOODIE_CONFIG.ENDPOINTS.RESTAURANTS,
                restaurantData
            );

            showRestaurantMessage(
                "Restaurant registered successfully!",
                "success"
            );

            restaurantForm.reset();
            console.log("Restaurant:", response);

        } catch (error) {
            showRestaurantMessage(error.message, "error");
        } finally {
            button.disabled = false;
            button.textContent = "Register Restaurant";
        }
    });
}

// ---------------- LOAD RESTAURANTS ----------------

async function loadRestaurants() {
    const restaurantList = document.getElementById("restaurantList");

    if (!restaurantList) return;

    if (!API.getAccessToken()) {
        window.location.href = "../login.html";
        return;
    }

    try {
        const restaurants = await API.get(
            FOODIE_CONFIG.ENDPOINTS.MY_RESTAURANTS
        );

        restaurantList.innerHTML = "";

        if (!Array.isArray(restaurants) || restaurants.length === 0) {
            restaurantList.textContent = "No restaurants registered yet.";
            return;
        }

        restaurants.forEach(restaurant => {
            const card = document.createElement("div");
            card.className = "restaurant-card";

            const heading = document.createElement("h3");
            heading.textContent = restaurant.name;

            const address = document.createElement("p");
            address.textContent =
                `${restaurant.address}, ${restaurant.city}`;

            const status = document.createElement("p");
            status.textContent = restaurant.is_active ? "Active" : "Inactive";

            const editButton = document.createElement("button");
            editButton.className = "btn";
            editButton.textContent = "Edit Details";
            editButton.addEventListener("click", () => {
                showEditForm(restaurant);
            });

            const statusButton = document.createElement("button");
            statusButton.className = restaurant.is_active
                ? "btn btn-danger"
                : "btn btn-success";

            statusButton.textContent = restaurant.is_active
                ? "Disable"
                : "Enable";

            statusButton.addEventListener("click", () => {
                changeRestaurantStatus(restaurant.id, restaurant.is_active);
            });

            card.append(heading, address, status, editButton, statusButton);
            restaurantList.appendChild(card);
        });

    } catch (error) {
        showRestaurantMessage(
            error.message,
            "error",
            "restaurantListMessage"
        );

        if (error.message.toLowerCase().includes("session") ||
            error.message.toLowerCase().includes("token")) {
            API.clearTokens();
            window.location.href = "../login.html";
        }
    }
}

// ---------------- EDIT RESTAURANT ----------------

function showEditForm(restaurant) {
    const name = prompt("Restaurant name:", restaurant.name);
    if (name === null) return;

    const address = prompt("Restaurant address:", restaurant.address);
    if (address === null) return;

    const city = prompt("City:", restaurant.city);
    if (city === null) return;

    const phone = prompt("Phone:", restaurant.phone || "");
    if (phone === null) return;

    const description = prompt(
        "Description:",
        restaurant.description || ""
    );
    if (description === null) return;

    updateRestaurant(restaurant.id, {
        name: name.trim(),
        address: address.trim(),
        city: city.trim(),
        phone: phone.trim() || null,
        description: description.trim() || null
    });
}

async function updateRestaurant(restaurantId, data) {
    try {
        await API.put(`/restaurants/${restaurantId}`, data);

        showRestaurantMessage(
            "Restaurant updated successfully!",
            "success",
            "restaurantListMessage"
        );

        await loadRestaurants();

    } catch (error) {
        showRestaurantMessage(
            error.message,
            "error",
            "restaurantListMessage"
        );
    }
}

// ---------------- ENABLE / DISABLE ----------------

async function changeRestaurantStatus(restaurantId, isActive) {
    const action = isActive ? "disable" : "enable";

    if (!confirm(`Are you sure you want to ${action} this restaurant?`)) {
        return;
    }

    try {
        await API.patch(
            `/restaurants/${restaurantId}/${action}`
        );

        showRestaurantMessage(
            `Restaurant ${action}d successfully!`,
            "success",
            "restaurantListMessage"
        );

        await loadRestaurants();

    } catch (error) {
        showRestaurantMessage(
            error.message,
            "error",
            "restaurantListMessage"
        );
    }
}

// ---------------- INITIALIZE ----------------

document.addEventListener("DOMContentLoaded", loadRestaurants);


// Restaurant Logo and Banner Upload

async function uploadRestaurantImage(imageType) {
    const restaurantId = document
        .getElementById("uploadRestaurantId").value.trim();

    const fileInput = document.getElementById(
        imageType === "logo" ? "restaurantLogo" : "restaurantBanner"
    );

    const messageElement = document.getElementById("imageUploadMessage");
    const button = document.getElementById(
        imageType === "logo" ? "uploadLogoButton" : "uploadBannerButton"
    );

    if (!restaurantId || Number(restaurantId) < 1) {
        showRestaurantMessage(
            "Please enter a valid restaurant ID.",
            "error",
            "imageUploadMessage"
        );
        return;
    }

    if (!fileInput.files.length) {
        showRestaurantMessage(
            `Please select a restaurant ${imageType} image.`,
            "error",
            "imageUploadMessage"
        );
        return;
    }

    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    button.disabled = true;
    button.textContent = "Uploading...";

    try {
        const response = await API.request(
            `/restaurants/${restaurantId}/${imageType}`,
            {
                method: "POST",
                body: formData
            }
        );

        showRestaurantMessage(
            response.message || `Restaurant ${imageType} uploaded successfully.`,
            "success",
            "imageUploadMessage"
        );

        fileInput.value = "";
        await loadRestaurants();

    } catch (error) {
        showRestaurantMessage(
            error.message || `Unable to upload restaurant ${imageType}.`,
            "error",
            "imageUploadMessage"
        );
    } finally {
        button.disabled = false;
        button.textContent =
            imageType === "logo" ? "Upload Logo" : "Upload Banner";
    }
}

document.getElementById("uploadLogoButton")?.addEventListener(
    "click",
    () => uploadRestaurantImage("logo")
);

document.getElementById("uploadBannerButton")?.addEventListener(
    "click",
    () => uploadRestaurantImage("banner")
);
