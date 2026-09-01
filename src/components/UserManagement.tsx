import React, { useState } from 'react';
import { 
  Users, 
  UserCheck, 
  Shield, 
  Plus, 
  Trash2, 
  Key, 
  Mail, 
  Check,
  Building,
  Lock
} from 'lucide-react';
import { DEMO_USERS } from '../data/mockData';
import { User, UserRole } from '../types';

interface UserManagementProps {
  currentUser: User;
  onSwitchUser: (user: User) => void;
}

export const UserManagement: React.FC<UserManagementProps> = ({
  currentUser,
  onSwitchUser
}) => {
  const [usersList, setUsersList] = useState<User[]>(DEMO_USERS);
  const [isCreatingUser, setIsCreatingUser] = useState<boolean>(false);
  const [name, setName] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [role, setRole] = useState<UserRole>('farmer');
  const [organization, setOrganization] = useState<string>('');

  const handleCreateUser = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email) return;

    const newUser: User = {
      id: `usr-${Date.now()}`,
      name,
      email,
      role,
      organization: organization || 'Agropecuaria Ceres',
      region: 'América Latina',
      preferences: {
        unitSystem: 'metric',
        theme: 'dark',
        autoSaveSimulations: true,
        highContrast3D: true,
        emailAlerts: true
      }
    };

    setUsersList([...usersList, newUser]);
    setIsCreatingUser(false);
    setName('');
    setEmail('');
    setOrganization('');
  };

  const getRoleBadge = (r: UserRole) => {
    switch (r) {
      case 'admin':
        return <span className="px-2 py-0.5 rounded-full bg-rose-500/20 text-rose-300 text-[10px] font-bold">Administrador</span>;
      case 'researcher':
        return <span className="px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 text-[10px] font-bold">Investigador / Científico</span>;
      case 'farmer':
        return <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-[10px] font-bold">Agricultor / Productor</span>;
      case 'consultant':
        return <span className="px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-300 text-[10px] font-bold">Consultor Agronómico</span>;
    }
  };

  return (
    <div id="user-management-module" className="bg-slate-900/90 rounded-2xl border border-slate-800 p-5 shadow-xl space-y-5">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <Users className="w-5 h-5 text-emerald-400" />
            Control de Acceso Basado en Roles (RBAC) & Usuarios
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Gestión de permisos diferenciados para Agricultores, Investigadores, Consultores y Administradores.
          </p>
        </div>

        <button
          id="btn-new-user-toggle"
          onClick={() => setIsCreatingUser(!isCreatingUser)}
          className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium flex items-center gap-1.5 shadow-md shadow-emerald-600/30 transition-all"
        >
          <Plus className="w-3.5 h-3.5" />
          Registrar Usuario
        </button>
      </div>

      {/* Switch Current User / Active Session Notice */}
      <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center font-bold text-white text-sm">
            {currentUser.name.charAt(0)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <strong className="text-sm text-slate-100">{currentUser.name}</strong>
              {getRoleBadge(currentUser.role)}
            </div>
            <p className="text-xs text-slate-400">{currentUser.email} • {currentUser.organization}</p>
          </div>
        </div>

        <div className="text-xs text-slate-400 flex items-center gap-1.5">
          <Lock className="w-3.5 h-3.5 text-emerald-400" />
          <span>Sesión JWT / OAuth2 Activa</span>
        </div>
      </div>

      {/* Inline Create User Form */}
      {isCreatingUser && (
        <form onSubmit={handleCreateUser} className="p-4 rounded-xl bg-slate-950/90 border border-emerald-500/40 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-emerald-300">Añadir Nuevo Usuario al Gemelo Digital</h3>
            <button type="button" onClick={() => setIsCreatingUser(false)} className="text-xs text-slate-400">Cancelar</button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1">Nombre Completo</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Dr. Roberto Silva"
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-100"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Email</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="roberto@campo.com"
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-100"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Organización / Empresa</label>
              <input
                type="text"
                value={organization}
                onChange={(e) => setOrganization(e.target.value)}
                placeholder="Instituto Nacional del Maíz"
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-100"
              />
            </div>
            <div>
              <label className="block text-slate-400 mb-1">Rol en el Sistema</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value as UserRole)}
                className="w-full px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-slate-100"
              >
                <option value="farmer">Agricultor / Productor</option>
                <option value="researcher">Investigador Científico</option>
                <option value="consultant">Consultor Agronómico</option>
                <option value="admin">Administrador del Sistema</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end pt-1">
            <button
              type="submit"
              className="px-4 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md shadow-emerald-600/30"
            >
              Guardar Usuario
            </button>
          </div>
        </form>
      )}

      {/* Users Table */}
      <div className="space-y-2">
        <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
          Usuarios con Acceso ({usersList.length})
        </div>

        <div className="space-y-2">
          {usersList.map((user) => {
            const isSelected = user.id === currentUser.id;
            return (
              <div
                key={user.id}
                className={`p-3.5 rounded-xl border flex flex-wrap items-center justify-between gap-3 transition-all ${
                  isSelected ? 'bg-emerald-950/30 border-emerald-500' : 'bg-slate-950/60 border-slate-800'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center font-bold text-slate-300 text-xs">
                    {user.name.charAt(0)}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-slate-200">{user.name}</span>
                      {getRoleBadge(user.role)}
                    </div>
                    <p className="text-xs text-slate-400">{user.email} • {user.organization}</p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {!isSelected ? (
                    <button
                      onClick={() => onSwitchUser(user)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-all"
                    >
                      Simular como este Usuario
                    </button>
                  ) : (
                    <span className="px-3 py-1 text-xs text-emerald-400 font-semibold flex items-center gap-1">
                      <Check className="w-3.5 h-3.5" /> Usuario Activo
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
