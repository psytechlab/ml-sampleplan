const methodSelect = document.querySelector("#method");
const form = document.querySelector("#calculator-form");
const fieldsContainer = document.querySelector("#fields");
const errorBox = document.querySelector("#error");
const resultPanel = document.querySelector("#result");
const summary = document.querySelector("#summary");
const limits = document.querySelector("#limits");
const jsonResult = document.querySelector("#json-result");
const submitButton = form.querySelector('button[type="submit"]');

let forms = {};

function selectedDistribution() {
  return form.elements.distribution?.value || "binomial";
}

function makeField(field) {
  const wrapper = document.createElement("div");
  wrapper.className = field.type === "checkbox" ? "field checkbox" : "field";
  wrapper.dataset.distribution = field.depends_on_distribution || "";

  const input = document.createElement(field.type === "select" ? "select" : "input");
  input.id = `field-${field.name}`;
  input.name = field.name;
  if (field.type !== "select") input.type = field.type;

  if (field.type === "select") {
    for (const optionValue of field.options) {
      const option = document.createElement("option");
      option.value = optionValue;
      option.textContent = optionValue;
      input.append(option);
    }
  }

  if (field.minimum !== null) input.min = field.minimum;
  if (field.maximum !== null) input.max = field.maximum;
  if (field.step !== null) input.step = field.step;
  if (field.default !== null) {
    if (field.type === "checkbox") input.checked = Boolean(field.default);
    else input.value = field.default;
  }
  input.required = field.required;

  const label = document.createElement("label");
  label.htmlFor = input.id;
  label.textContent = field.label;

  if (field.type === "checkbox") wrapper.append(input, label);
  else wrapper.append(label, input);

  if (field.help) {
    const help = document.createElement("small");
    help.textContent = field.help;
    wrapper.append(help);
  }
  return wrapper;
}

function updateConditionalFields() {
  const distribution = selectedDistribution();
  for (const wrapper of fieldsContainer.querySelectorAll("[data-distribution]")) {
    const dependency = wrapper.dataset.distribution;
    const visible = !dependency || dependency === distribution;
    wrapper.hidden = !visible;
    for (const input of wrapper.querySelectorAll("input, select")) input.disabled = !visible;
  }

  const ciMethod = form.elements.method;
  if (ciMethod) {
    const agresti = [...ciMethod.options].find((option) => option.value === "agresti-coull");
    if (agresti) agresti.disabled = distribution === "hypergeometric";
    if (ciMethod.selectedOptions[0]?.disabled) ciMethod.value = "exact";
  }
}

function renderForm() {
  fieldsContainer.replaceChildren(...forms[methodSelect.value].fields.map(makeField));
  form.elements.distribution?.addEventListener("change", updateConditionalFields);
  updateConditionalFields();
  errorBox.hidden = true;
  resultPanel.hidden = true;
}

function payloadFromForm() {
  const payload = {};
  for (const [name, value] of new FormData(form).entries()) {
    const input = form.elements[name];
    if (input.type === "number" && value === "") continue;
    if (input.type === "checkbox") payload[name] = input.checked;
    else if (input.type === "number") payload[name] = Number(value);
    else payload[name] = value;
  }
  for (const input of form.querySelectorAll('input[type="checkbox"]:not(:disabled)')) {
    if (!(input.name in payload)) payload[input.name] = false;
  }
  return payload;
}

function renderResult(data) {
  const importantKeys = {
    ci: ["n"],
    single: ["n", "c"],
    double: ["n", "c1", "c2", "average_sample_size", "average_sample_size_curtailed"],
    sequential: ["average_sample_number", "average_sample_number_curtailed", "cutoff"],
  }[methodSelect.value];

  summary.replaceChildren(
    ...importantKeys.filter((key) => key in data).map((key) => {
      const card = document.createElement("div");
      const label = document.createElement("span");
      const value = document.createElement("strong");
      label.textContent = key.replaceAll("_", " ");
      value.textContent = typeof data[key] === "number" ? Number(data[key].toFixed(4)) : data[key];
      card.append(label, value);
      return card;
    }),
  );

  limits.replaceChildren();
  if (data.lower_limits && data.upper_limits) {
    const table = document.createElement("table");
    table.innerHTML =
      "<thead><tr><th>Inspected</th><th>Accept at or below</th><th>Reject at or above</th></tr></thead>";
    const body = document.createElement("tbody");
    data.lower_limits.forEach((lower, index) => {
      const row = document.createElement("tr");
      for (const value of [index, lower ?? "—", data.upper_limits[index] ?? "—"]) {
        const cell = document.createElement("td");
        cell.textContent = value;
        row.append(cell);
      }
      body.append(row);
    });
    table.append(body);
    limits.append(table);
  }

  jsonResult.textContent = JSON.stringify(data, null, 2);
  resultPanel.hidden = false;
}

function errorMessage(body) {
  if (typeof body.detail === "string") return body.detail;
  if (Array.isArray(body.detail)) return body.detail.map((item) => item.msg).join("; ");
  return "The calculation could not be completed.";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  resultPanel.hidden = true;
  submitButton.disabled = true;
  submitButton.textContent = "Calculating…";
  form.setAttribute("aria-busy", "true");
  try {
    const response = await fetch(`/api/${methodSelect.value}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payloadFromForm()),
    });
    const responseText = await response.text();
    let body;
    try {
      body = JSON.parse(responseText);
    } catch {
      body = { detail: responseText || `Request failed with HTTP ${response.status}.` };
    }
    if (!response.ok) throw new Error(errorMessage(body));
    renderResult(body);
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.hidden = false;
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Calculate";
    form.removeAttribute("aria-busy");
  }
});

async function start() {
  try {
    const response = await fetch("/api/forms");
    if (!response.ok) throw new Error("Could not load form descriptions.");
    forms = await response.json();
    for (const [name, spec] of Object.entries(forms)) {
      const option = document.createElement("option");
      option.value = name;
      option.textContent = spec.label;
      methodSelect.append(option);
    }
    methodSelect.addEventListener("change", renderForm);
    renderForm();
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.hidden = false;
  }
}

start();
