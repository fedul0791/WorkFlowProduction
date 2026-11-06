import { EmployeeProfile } from "@/components/employee-profile";
import { AppShell } from "@/components/app-shell";
export default async function Page({params}:{params:Promise<{id:string}>}){const {id}=await params;return <AppShell locale="de" active="personnel"><EmployeeProfile locale="de" employeeId={id}/></AppShell>}
