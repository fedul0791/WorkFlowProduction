import { useState } from "react";
import { useNFC } from "react-nfc";

const RegisterNFC = () => {
    const { data, error } = useNFC();
    const [name, setName] = useState("");
    const [role, setRole] = useState("user");

    const handleRegister = async () => {
        if (!data) return alert("NFC-чип не найден");
        const response = await fetch("http://localhost:8000/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nfc_chip_id: data, name, role })
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
            <h2>Регистрация через NFC</h2>
            <input
                placeholder="Имя"
                value={name}
                onChange={(e) => setName(e.target.value)}
            />
            <select value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="user">Пользователь</option>
                <option value="admin">Админ</option>
            </select>
            <button onClick={handleRegister}>Зарегистрировать</button>
            {error && <p style={{ color: "red" }}>{error}</p>}
        </div>
    );
};

export default RegisterNFC;