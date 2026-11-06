import { useState } from "react";

const RegisterManual = () => {
    const [name, setName] = useState("");
    const [role, setRole] = useState("user");
    const [manualData, setManualData] = useState({});

    const handleRegister = async () => {
        const response = await fetch("http://localhost:8000/register/manual", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, role, manual_data: manualData })
        });
        const result = await response.json();
        if (result.status === "success") {
            alert("Регистрация успешна!");
        } else {
            alert("Ошибка: " + result.error);
        }
    };

    return (
        <div>
            <h2>Ручная регистрация</h2>
            <input
                placeholder="Имя"
                value={name}
                onChange={(e) => setName(e.target.value)}
            />
            <select value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="user">Пользователь</option>
                <option value="admin">Админ</option>
            </select>
            <textarea
                placeholder="Дополнительные данные (JSON)"
                value={JSON.stringify(manualData)}
                onChange={(e) => setManualData(JSON.parse(e.target.value))}
            />
            <button onClick={handleRegister}>Зарегистрировать</button>
        </div>
    );
};

export default RegisterManual;