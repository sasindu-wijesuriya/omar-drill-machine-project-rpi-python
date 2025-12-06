// GPIO Simulator Client-side Script

let socket;
let pinsState = {};

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
  initWebSocket();
  initEventListeners();
  generatePinGrid();
  fetchPins();
});

// WebSocket Connection
function initWebSocket() {
  socket = io();

  socket.on("connect", () => {
    updateConnectionStatus(true);
    addLog("Connected to simulator", "info");
  });

  socket.on("disconnect", () => {
    updateConnectionStatus(false);
    addLog("Disconnected from simulator", "error");
  });

  socket.on("connected", (data) => {
    console.log("Connected:", data);
    pinsState = data.pins;
    updateUI();
  });

  socket.on("pins_update", (data) => {
    pinsState = data.pins;
    updateUI();
  });

  socket.on("pin_changed", (data) => {
    if (pinsState[data.pin]) {
      pinsState[data.pin].value = data.value;
      updatePinUI(data.pin);

      const pinName = pinsState[data.pin].name;
      const mode = pinsState[data.pin].mode;
      addLog(`Pin ${data.pin} (${pinName}) [${mode}] → ${data.value}`, "info");
    }
  });

  socket.on("simulator_reset", () => {
    addLog("Simulator reset to default state", "warning");
    fetchPins();
  });
}

// Update connection status indicator
function updateConnectionStatus(connected) {
  const statusIndicator = document.getElementById("connection-status");
  const statusDot = statusIndicator.querySelector(".status-dot");

  if (connected) {
    statusDot.classList.remove("offline");
    statusDot.classList.add("online");
    statusIndicator.innerHTML =
      '<span class="status-dot online"></span> Connected';
  } else {
    statusDot.classList.remove("online");
    statusDot.classList.add("offline");
    statusIndicator.innerHTML =
      '<span class="status-dot offline"></span> Disconnected';
  }
}

// Event Listeners
function initEventListeners() {
  // Reset button
  document
    .getElementById("reset-btn")
    .addEventListener("click", resetSimulator);

  // Button controls
  document
    .querySelectorAll('.control-btn[data-type="button"]')
    .forEach((btn) => {
      btn.addEventListener("mousedown", () => pressButton(btn));
      btn.addEventListener("mouseup", () => releaseButton(btn));
      btn.addEventListener("mouseleave", () => releaseButton(btn));

      // Touch support
      btn.addEventListener("touchstart", (e) => {
        e.preventDefault();
        pressButton(btn);
      });
      btn.addEventListener("touchend", (e) => {
        e.preventDefault();
        releaseButton(btn);
      });
    });

  // Limit switches
  document
    .querySelectorAll('.switch-control input[type="checkbox"]')
    .forEach((checkbox) => {
      checkbox.addEventListener("change", () => toggleSwitch(checkbox));
    });
}

// Generate GPIO pin grid (40-pin header)
function generatePinGrid() {
  const pinGrid = document.getElementById("pin-grid");

  // Raspberry Pi 40-pin header layout
  const pinLayout = [
    // [physical_pin, gpio_number, name, is_gpio]
    [1, null, "3.3V", false],
    [2, null, "5V", false],
    [3, 2, "GPIO2", true],
    [4, null, "5V", false],
    [5, 3, "GPIO3", true],
    [6, null, "GND", false],
    [7, 4, "GPIO4", true],
    [8, 14, "GPIO14", true],
    [9, null, "GND", false],
    [10, 15, "GPIO15", true],
    [11, 17, "GPIO17", true],
    [12, 18, "GPIO18", true],
    [13, 27, "GPIO27", true],
    [14, null, "GND", false],
    [15, 22, "GPIO22", true],
    [16, 23, "GPIO23", true],
    [17, null, "3.3V", false],
    [18, 24, "GPIO24", true],
    [19, 10, "GPIO10", true],
    [20, null, "GND", false],
    [21, 9, "GPIO9", true],
    [22, 25, "GPIO25", true],
    [23, 11, "GPIO11", true],
    [24, 8, "GPIO8", true],
    [25, null, "GND", false],
    [26, 7, "GPIO7", true],
    [27, 0, "GPIO0", true],
    [28, 1, "GPIO1", true],
    [29, 5, "GPIO5", true],
    [30, null, "GND", false],
    [31, 6, "GPIO6", true],
    [32, 12, "GPIO12", true],
    [33, 13, "GPIO13", true],
    [34, null, "GND", false],
    [35, 19, "GPIO19", true],
    [36, 16, "GPIO16", true],
    [37, 26, "GPIO26", true],
    [38, 20, "GPIO20", true],
    [39, null, "GND", false],
    [40, 21, "GPIO21", true],
  ];

  for (let i = 0; i < pinLayout.length; i += 2) {
    const leftPin = pinLayout[i];
    const rightPin = pinLayout[i + 1];

    pinGrid.appendChild(createPinElement(leftPin, "left"));
    pinGrid.appendChild(createPinElement(rightPin, "right"));
  }
}

// Create pin element
function createPinElement(pinData, side) {
  const [physicalPin, gpioNum, name, isGpio] = pinData;
  const pin = document.createElement("div");
  pin.className = `pin ${side}`;

  if (!isGpio) {
    pin.classList.add("power");
    pin.innerHTML = `
            <span class="pin-number">${physicalPin}</span>
            <span class="pin-name">${name}</span>
        `;
  } else {
    pin.dataset.gpio = gpioNum;

    const state = pinsState[gpioNum];
    if (state) {
      pin.classList.add(state.mode.toLowerCase());
      if (state.value === 1) {
        pin.classList.add("high");
      }
    }

    const pinName = state ? state.name : name;
    const pinMode = state ? state.mode : "N/A";

    pin.innerHTML = `
            <span class="pin-number">${physicalPin}</span>
            <span class="pin-gpio">GPIO${gpioNum}</span>
            <span class="pin-name">${pinName}</span>
            <span class="pin-value" data-pin="${gpioNum}">${
      state ? state.value : "?"
    }</span>
        `;

    // Add click handler for input pins
    if (state && state.mode === "INPUT") {
      pin.style.cursor = "pointer";
      pin.addEventListener("click", () => togglePin(gpioNum));
    }
  }

  return pin;
}

// Fetch current pin states
async function fetchPins() {
  try {
    const response = await fetch("/api/pins");
    const data = await response.json();
    pinsState = data.pins;

    // Handle pulse activity
    if (data.pulse_activity) {
      updatePulseActivity(data.pulse_activity);
    }

    updateUI();
  } catch (error) {
    console.error("Error fetching pins:", error);
    addLog("Error fetching pin states", "error");
  }
}

// Update pulse activity indicators
function updatePulseActivity(pulseActivity) {
  Object.keys(pulseActivity).forEach((pin) => {
    const activity = pulseActivity[pin];
    const ledIndicator = document.querySelector(
      `.led-indicator[data-pin="${pin}"]`
    );

    if (ledIndicator) {
      if (activity.active) {
        // Add pulsing animation
        ledIndicator.classList.add("active", "pulsing");
        addLog(`Pin ${pin} is pulsing (${activity.count} pulses)`, "info");
      } else {
        // Remove pulsing animation if inactive
        ledIndicator.classList.remove("pulsing");
      }
    }
  });
}

// Toggle pin (for INPUT pins in the grid)
async function togglePin(pin) {
  try {
    const response = await fetch(`/api/pin/${pin}/toggle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await response.json();

    if (data.success) {
      const pinName = pinsState[pin].name;
      addLog(`Pin ${pin} (${pinName}) toggled to ${data.value}`, "info");
    }
  } catch (error) {
    console.error("Error toggling pin:", error);
    addLog(`Error toggling pin ${pin}`, "error");
  }
}

// Press button (set to LOW - active low with pull-up)
async function pressButton(btnElement) {
  const pin = parseInt(btnElement.dataset.pin);
  btnElement.classList.add("pressed");

  const stateSpan = btnElement.querySelector(".btn-state");
  stateSpan.textContent = "Pressed";

  try {
    await fetch(`/api/pin/${pin}/value`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value: 0 }), // LOW when pressed
    });

    const pinName = pinsState[pin].name;
    addLog(`${pinName} button pressed (GPIO ${pin} → 0)`, "info");
  } catch (error) {
    console.error("Error pressing button:", error);
  }
}

// Release button (set to HIGH - pull-up default)
async function releaseButton(btnElement) {
  const pin = parseInt(btnElement.dataset.pin);
  btnElement.classList.remove("pressed");

  const stateSpan = btnElement.querySelector(".btn-state");
  stateSpan.textContent = "Released";

  try {
    await fetch(`/api/pin/${pin}/value`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value: 1 }), // HIGH when released
    });

    const pinName = pinsState[pin].name;
    addLog(`${pinName} button released (GPIO ${pin} → 1)`, "info");
  } catch (error) {
    console.error("Error releasing button:", error);
  }
}

// Toggle switch
async function toggleSwitch(checkbox) {
  const pin = parseInt(checkbox.dataset.pin);
  const triggered = checkbox.checked;

  try {
    await fetch(`/api/pin/${pin}/value`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ value: triggered ? 0 : 1 }), // Active LOW
    });

    const pinName = pinsState[pin].name;
    const status = triggered ? "TRIGGERED (0)" : "RELEASED (1)";
    addLog(`${pinName} ${status}`, triggered ? "warning" : "info");
  } catch (error) {
    console.error("Error toggling switch:", error);
  }
}

// Reset simulator
async function resetSimulator() {
  if (!confirm("Reset all pins to default state?")) return;

  try {
    const response = await fetch("/api/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    const data = await response.json();

    if (data.success) {
      addLog("Simulator reset", "warning");

      // Reset UI controls
      document.querySelectorAll(".control-btn").forEach((btn) => {
        btn.classList.remove("pressed");
        btn.querySelector(".btn-state").textContent = "Released";
      });

      document
        .querySelectorAll('.switch-control input[type="checkbox"]')
        .forEach((cb) => {
          cb.checked = false;
        });

      fetchPins();
    }
  } catch (error) {
    console.error("Error resetting simulator:", error);
    addLog("Error resetting simulator", "error");
  }
}

// Update UI
function updateUI() {
  Object.keys(pinsState).forEach((pin) => {
    updatePinUI(parseInt(pin));
  });
}

// Update specific pin UI
function updatePinUI(pin) {
  const state = pinsState[pin];
  if (!state) return;

  // Update pin grid
  const pinElement = document.querySelector(`.pin[data-gpio="${pin}"]`);
  if (pinElement) {
    pinElement.className = `pin ${
      pinElement.classList.contains("left") ? "left" : "right"
    }`;
    pinElement.classList.add(state.mode.toLowerCase());

    if (state.value === 1) {
      pinElement.classList.add("high");
    }

    const valueSpan = pinElement.querySelector(".pin-value");
    if (valueSpan) {
      valueSpan.textContent = state.value;
    }
  }

  // Update motor indicators
  const ledIndicator = document.querySelector(
    `.led-indicator[data-pin="${pin}"]`
  );
  if (ledIndicator) {
    if (state.value === 1) {
      ledIndicator.classList.add("active");
    } else {
      ledIndicator.classList.remove("active");
    }
  }

  const pinValueSpan = document.querySelector(`.pin-value[data-pin="${pin}"]`);
  if (pinValueSpan && !pinValueSpan.closest(".pin")) {
    pinValueSpan.textContent = state.value;
  }
}

// Add log entry
function addLog(message, level = "info") {
  const logContent = document.getElementById("activity-log");
  const timestamp = new Date().toLocaleTimeString();

  const entry = document.createElement("p");
  entry.className = `log-entry ${level}`;
  entry.textContent = `[${timestamp}] ${message}`;

  logContent.insertBefore(entry, logContent.firstChild);

  // Keep only last 50 entries
  while (logContent.children.length > 50) {
    logContent.removeChild(logContent.lastChild);
  }
}

// Auto-refresh pins every 2 seconds (backup to WebSocket)
setInterval(() => {
  socket.emit("request_pins");
}, 2000);
