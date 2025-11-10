import AutomationInput from "../AutomationInput";

export default function AutomationInputExample() {
  return (
    <AutomationInput
      onExecute={(data) => console.log("Execute automation:", data)}
      isExecuting={false}
    />
  );
}
