"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import type { FormEvent } from "react";
import type { Locale } from "@/i18n/messages";
import { api } from "@/lib/api";
const labels={de:{title:"Anmelden",email:"E-Mail",password:"Passwort",submit:"Anmelden"},ru:{title:"Вход",email:"Электронная почта",password:"Пароль",submit:"Войти"},en:{title:"Sign in",email:"Email",password:"Password",submit:"Sign in"}};
export function LoginForm({locale}:{locale:Locale}){
 const t=labels[locale],router=useRouter();const[email,setEmail]=useState(""),[password,setPassword]=useState(""),[error,setError]=useState(""),[busy,setBusy]=useState(false);
 async function submit(e:FormEvent){e.preventDefault();setBusy(true);setError("");try{await api("/api/v1/auth/login",{method:"POST",body:JSON.stringify({email,password})});router.replace(`/${locale}/betrieb`);router.refresh()}catch(err){setError(err instanceof Error?err.message:t.title)}finally{setBusy(false)}}
 return <main className="content"><section className="auth-card"><span className="eyebrow">WorkFlow Production</span><h1>{t.title}</h1><form className="enterprise-form" onSubmit={submit}><label>{t.email}<input type="email" autoComplete="username" required value={email} onChange={e=>setEmail(e.target.value)}/></label><label>{t.password}<input type="password" autoComplete="current-password" required value={password} onChange={e=>setPassword(e.target.value)}/></label>{error&&<div className="enterprise-error" role="alert">{error}</div>}<button className="primary-button" disabled={busy}>{busy?"…":t.submit}</button></form></section></main>
}
