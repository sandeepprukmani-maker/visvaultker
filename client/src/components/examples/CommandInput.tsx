import { CommandInput } from "../command-input"

export default function CommandInputExample() {
  return (
    <div className="p-6 max-w-4xl">
      <CommandInput onExecute={(cmd) => console.log("Execute:", cmd)} />
    </div>
  )
}
