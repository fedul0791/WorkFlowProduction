import { EmployeeProfile } from "@/components/employee-profile";
import { AppShell } from "@/components/app-shell";
export default async function Page({params}:{params:Promise<{id:string}>}){const {id}=await params;return <AppShell locale="en" active="personnel"><EmployeeProfile locale="en" employeeId={id}/></AppShell>}
