import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Plus, Edit2, Trash2, Shield, Users, Layers, Layout, AlertCircle } from 'lucide-react';

export const Management: React.FC = () => {
  const { token, user } = useAuth();
  const [activeSubTab, setActiveSubTab] = useState<'PLANTS' | 'DEPTS' | 'MACHINES' | 'DEVICES' | 'USERS'>('PLANTS');
  
  // Entity states
  const [plants, setPlants] = useState<any[]>([]);
  const [depts, setDepts] = useState<any[]>([]);
  const [machines, setMachines] = useState<any[]>([]);
  const [devices, setDevices] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);

  // Modal Form State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'ADD' | 'EDIT'>('ADD');
  const [editId, setEditId] = useState<number | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Form Fields State
  const [plantForm, setPlantForm] = useState({ name: '', location: '', timezone: 'EST', description: '', status: 'ACTIVE' });
  const [deptForm, setDeptForm] = useState({ plant_id: 1, name: '', description: '' });
  const [machineForm, setMachineForm] = useState({ department_id: 1, name: '', type: 'SMS_SHOP', rated_capacity: 70000, status: 'STOPPED' });
  const [deviceForm, setDeviceForm] = useState({ machine_id: 1, name: '', type: 'POWER', register_address: '30001', unit: 'kW', nominal_min: 0, nominal_max: 50000, serial_number: '', firmware_version: 'v1.0.0', communication_status: 'ONLINE', is_active: true });
  const [userForm, setUserForm] = useState({ username: '', email: '', password: '', role_id: 2, is_active: true });

  useEffect(() => {
    fetchAll();
  }, [token, activeSubTab]);

  const fetchAll = () => {
    if (activeSubTab === 'PLANTS') fetchPlants();
    if (activeSubTab === 'DEPTS') fetchDepts();
    if (activeSubTab === 'MACHINES') fetchMachines();
    if (activeSubTab === 'DEVICES') fetchDevices();
    if (activeSubTab === 'USERS') fetchUsers();
  };

  const fetchPlants = async () => {
    try {
      const res = await fetch('/api/plants', { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) setPlants(await res.json());
      else setPlants([]);
    } catch {
      setPlants([]);
    }
  };

  const fetchDepts = async () => {
    try {
      const res = await fetch('/api/departments', { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) setDepts(await res.json());
      else setDepts([]);
    } catch {
      setDepts([]);
    }
  };

  const fetchMachines = async () => {
    try {
      const res = await fetch('/api/machines', { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) setMachines(await res.json());
      else setMachines([]);
    } catch {
      setMachines([]);
    }
  };

  const fetchDevices = async () => {
    try {
      const res = await fetch('/api/devices', { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) setDevices(await res.json());
      else setDevices([]);
    } catch {
      setDevices([]);
    }
  };

  const fetchUsers = async () => {
    try {
      const res = await fetch('/api/users', { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) setUsers(await res.json());
      else setUsers([]);
    } catch {
      setUsers([]);
    }
  };

  const handleOpenAdd = () => {
    setModalMode('ADD');
    setEditId(null);
    setErrorMsg(null);
    // Reset forms
    setPlantForm({ name: '', location: '', timezone: 'EST', description: '', status: 'ACTIVE' });
    setDeptForm({ plant_id: plants[0]?.id || 1, name: '', description: '' });
    setMachineForm({ department_id: depts[0]?.id || 1, name: '', type: 'SMS_SHOP', rated_capacity: 70000, status: 'STOPPED' });
    setDeviceForm({ machine_id: machines[0]?.id || 1, name: '', type: 'POWER', register_address: '', unit: 'kW', nominal_min: 0, nominal_max: 50000, serial_number: '', firmware_version: 'v1.0.0', communication_status: 'ONLINE', is_active: true });
    setUserForm({ username: '', email: '', password: '', role_id: 2, is_active: true });
    setIsModalOpen(true);
  };

  const handleOpenEdit = (item: any) => {
    setModalMode('EDIT');
    setEditId(item.id);
    setErrorMsg(null);
    
    if (activeSubTab === 'PLANTS') setPlantForm({ name: item.name, location: item.location || '', timezone: item.timezone || 'EST', description: item.description || '', status: item.status || 'ACTIVE' });
    if (activeSubTab === 'DEPTS') setDeptForm({ plant_id: item.plant_id, name: item.name, description: item.description || '' });
    if (activeSubTab === 'MACHINES') setMachineForm({ department_id: item.department_id, name: item.name, type: item.type, rated_capacity: item.rated_capacity, status: item.status });
    if (activeSubTab === 'DEVICES') setDeviceForm({ machine_id: item.machine_id, name: item.name, type: item.type, register_address: item.register_address, unit: item.unit, nominal_min: item.nominal_min || 0, nominal_max: item.nominal_max || 50000, serial_number: item.serial_number || '', firmware_version: item.firmware_version || 'v1.0.0', communication_status: item.communication_status || 'ONLINE', is_active: item.is_active });
    if (activeSubTab === 'USERS') setUserForm({ username: item.username, email: item.email, password: '', role_id: item.role_id, is_active: item.is_active });
    
    setIsModalOpen(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this resource?")) return;
    const endpoint = activeSubTab === 'PLANTS' ? `/api/plants/${id}`
      : activeSubTab === 'DEPTS' ? `/api/departments/${id}`
      : activeSubTab === 'MACHINES' ? `/api/machines/${id}`
      : activeSubTab === 'DEVICES' ? `/api/devices/${id}`
      : `/api/users/${id}`;
      
    try {
      const res = await fetch(endpoint, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        fetchAll();
      } else {
        const err = await res.json();
        alert(err.detail || "Delete operation failed.");
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    let payload = {};
    let endpoint = '';
    
    if (activeSubTab === 'PLANTS') {
      payload = plantForm;
      endpoint = modalMode === 'ADD' ? '/api/plants' : `/api/plants/${editId}`;
    } else if (activeSubTab === 'DEPTS') {
      payload = deptForm;
      endpoint = modalMode === 'ADD' ? '/api/departments' : `/api/departments/${editId}`;
    } else if (activeSubTab === 'MACHINES') {
      payload = machineForm;
      endpoint = modalMode === 'ADD' ? '/api/machines' : `/api/machines/${editId}`;
    } else if (activeSubTab === 'DEVICES') {
      payload = deviceForm;
      endpoint = modalMode === 'ADD' ? '/api/devices' : `/api/devices/${editId}`;
    } else if (activeSubTab === 'USERS') {
      payload = userForm;
      endpoint = modalMode === 'ADD' ? '/api/users' : `/api/users/${editId}`;
    }

    try {
      const res = await fetch(endpoint, {
        method: modalMode === 'ADD' ? 'POST' : 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        setIsModalOpen(false);
        fetchAll();
      } else {
        const data = await res.json();
        setErrorMsg(data.detail || "Operation failed. Review input constraints.");
      }
    } catch (err) {
      setErrorMsg("Server unreachable.");
    }
  };

  const subTabs = [
    { key: 'PLANTS', name: 'Plants', icon: Shield, adminOnly: false },
    { key: 'DEPTS', name: 'Departments', icon: Layers, adminOnly: false },
    { key: 'MACHINES', name: 'Machines', icon: Layout, adminOnly: false },
    { key: 'DEVICES', name: 'Devices', icon: Layout, adminOnly: false },
    { key: 'USERS', name: 'User Accounts', icon: Users, adminOnly: true }
  ];

  return (
    <div className="space-y-6 animate-fade-in text-xs font-semibold">
      
      {/* Tab Selectors */}
      <div className="flex flex-wrap gap-2 pb-2 border-b border-[#1F2942]/40">
        {subTabs.map(tab => {
          if (tab.adminOnly && user?.role !== 'Admin') return null;
          const Icon = tab.icon;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveSubTab(tab.key as any)}
              className={`px-4 py-2.5 rounded-xl font-bold transition flex items-center gap-2 ${
                activeSubTab === tab.key
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/10'
                  : 'bg-[#101529]/60 text-slate-450 hover:bg-[#1A233D] hover:text-slate-200 border border-[#1F2942]/40'
              }`}
            >
              <Icon className="h-4 w-4" /> {tab.name}
            </button>
          );
        })}
      </div>

      {/* Main Grid View */}
      <div className="bg-[#0F1424]/90 border border-[#1F2942]/60 rounded-2xl overflow-hidden shadow-2xl backdrop-blur">
        <div className="p-5 border-b border-[#1F2942]/80 bg-[#151C36]/50 flex justify-between items-center">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-widest">
            Manage {activeSubTab.toLowerCase()} entries
          </h4>
          <button 
            onClick={handleOpenAdd}
            className="bg-blue-600 hover:bg-blue-700 text-white font-extrabold px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition"
          >
            <Plus className="h-4 w-4" /> Add New
          </button>
        </div>

        {/* Dynamic Tables rendering */}
        <div className="overflow-x-auto">
          {activeSubTab === 'PLANTS' && (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#0A0E1A] text-[#556994] font-bold border-b border-[#1F2942]/50 text-[10px] uppercase">
                  <th className="p-4 pl-6">ID</th>
                  <th className="p-4">Plant Name</th>
                  <th className="p-4">Location</th>
                  <th className="p-4">Timezone</th>
                  <th className="p-4">Description</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 pr-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1F2942]/40">
                {plants.map(p => (
                  <tr key={p.id} className="hover:bg-[#151C36]/20 transition">
                    <td className="p-4 pl-6 font-mono text-[#556994]">#{p.id}</td>
                    <td className="p-4 font-bold text-slate-200">{p.name}</td>
                    <td className="p-4 text-slate-400">{p.location}</td>
                    <td className="p-4 text-slate-400 font-mono">{p.timezone}</td>
                    <td className="p-4 text-slate-400 max-w-xs overflow-hidden text-ellipsis whitespace-nowrap">{p.description}</td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${p.status === 'ACTIVE' ? 'bg-emerald-950/20 text-emerald-400' : 'bg-red-950/20 text-red-400'}`}>{p.status}</span>
                    </td>
                    <td className="p-4 pr-6 text-right space-x-2">
                      <button onClick={() => handleOpenEdit(p)} className="p-1 rounded bg-[#20294A] text-slate-300 hover:text-white"><Edit2 className="h-3.5 w-3.5" /></button>
                      <button onClick={() => handleDelete(p.id)} className="p-1 rounded bg-red-950/20 text-red-450 hover:text-red-400"><Trash2 className="h-3.5 w-3.5" /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeSubTab === 'DEPTS' && (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#0A0E1A] text-[#556994] font-bold border-b border-[#1F2942]/50 text-[10px] uppercase">
                  <th className="p-4 pl-6">ID</th>
                  <th className="p-4">Department Name</th>
                  <th className="p-4">Plant ID</th>
                  <th className="p-4">Description</th>
                  <th className="p-4 pr-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1F2942]/40">
                {depts.map(d => (
                  <tr key={d.id} className="hover:bg-[#151C36]/20 transition">
                    <td className="p-4 pl-6 font-mono text-[#556994]">#{d.id}</td>
                    <td className="p-4 font-bold text-slate-200">{d.name}</td>
                    <td className="p-4 text-slate-400 font-mono">#{d.plant_id}</td>
                    <td className="p-4 text-slate-400 max-w-xs overflow-hidden text-ellipsis">{d.description}</td>
                    <td className="p-4 pr-6 text-right space-x-2">
                      <button onClick={() => handleOpenEdit(d)} className="p-1 rounded bg-[#20294A] text-slate-300 hover:text-white"><Edit2 className="h-3.5 w-3.5" /></button>
                      <button onClick={() => handleDelete(d.id)} className="p-1 rounded bg-red-950/20 text-red-450 hover:text-red-400"><Trash2 className="h-3.5 w-3.5" /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeSubTab === 'MACHINES' && (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#0A0E1A] text-[#556994] font-bold border-b border-[#1F2942]/50 text-[10px] uppercase">
                  <th className="p-4 pl-6">ID</th>
                  <th className="p-4">Machine Name</th>
                  <th className="p-4">Machine Type</th>
                  <th className="p-4 font-mono">Rated Capacity</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 pr-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1F2942]/40">
                {machines.map(m => (
                  <tr key={m.id} className="hover:bg-[#151C36]/20 transition">
                    <td className="p-4 pl-6 font-mono text-[#556994]">#{m.id}</td>
                    <td className="p-4 font-bold text-slate-200">{m.name}</td>
                    <td className="p-4 text-slate-400">{m.type}</td>
                    <td className="p-4 font-mono text-cyan-400">{m.rated_capacity?.toLocaleString()} kW</td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${m.status === 'RUNNING' ? 'bg-emerald-950/20 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>{m.status}</span>
                    </td>
                    <td className="p-4 pr-6 text-right space-x-2">
                      <button onClick={() => handleOpenEdit(m)} className="p-1 rounded bg-[#20294A] text-slate-300 hover:text-white"><Edit2 className="h-3.5 w-3.5" /></button>
                      <button onClick={() => handleDelete(m.id)} className="p-1 rounded bg-red-950/20 text-red-450 hover:text-red-400"><Trash2 className="h-3.5 w-3.5" /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeSubTab === 'DEVICES' && (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#0A0E1A] text-[#556994] font-bold border-b border-[#1F2942]/50 text-[10px] uppercase">
                  <th className="p-4 pl-6">ID</th>
                  <th className="p-4">Device Name</th>
                  <th className="p-4">Type</th>
                  <th className="p-4">Register</th>
                  <th className="p-4">Unit</th>
                  <th className="p-4">Serial Number</th>
                  <th className="p-4 pr-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1F2942]/40">
                {devices.map(d => (
                  <tr key={d.id} className="hover:bg-[#151C36]/20 transition">
                    <td className="p-4 pl-6 font-mono text-[#556994]">#{d.id}</td>
                    <td className="p-4 font-bold text-slate-200">{d.name}</td>
                    <td className="p-4 text-slate-400">{d.type}</td>
                    <td className="p-4 font-mono text-slate-400">{d.register_address}</td>
                    <td className="p-4 text-slate-400 font-bold">{d.unit || '-'}</td>
                    <td className="p-4 font-mono text-slate-500">{d.serial_number}</td>
                    <td className="p-4 pr-6 text-right space-x-2">
                      <button onClick={() => handleOpenEdit(d)} className="p-1 rounded bg-[#20294A] text-slate-300 hover:text-white"><Edit2 className="h-3.5 w-3.5" /></button>
                      <button onClick={() => handleDelete(d.id)} className="p-1 rounded bg-red-950/20 text-red-450 hover:text-red-400"><Trash2 className="h-3.5 w-3.5" /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeSubTab === 'USERS' && (
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#0A0E1A] text-[#556994] font-bold border-b border-[#1F2942]/50 text-[10px] uppercase">
                  <th className="p-4 pl-6">ID</th>
                  <th className="p-4">Username</th>
                  <th className="p-4">Email</th>
                  <th className="p-4">Role level</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 pr-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1F2942]/40">
                {users.map(u => (
                  <tr key={u.id} className="hover:bg-[#151C36]/20 transition">
                    <td className="p-4 pl-6 font-mono text-[#556994]">#{u.id}</td>
                    <td className="p-4 font-bold text-slate-200">{u.username}</td>
                    <td className="p-4 text-slate-400">{u.email}</td>
                    <td className="p-4 font-mono">
                      <span className="bg-[#131930] px-2 py-0.5 border border-[#1F2942] rounded text-[10px]">Role ID {u.role_id}</span>
                    </td>
                    <td className="p-4">
                      <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${u.is_active ? 'bg-emerald-950/20 text-emerald-400' : 'bg-red-950/20 text-red-400'}`}>{u.is_active ? 'ACTIVE' : 'INACTIVE'}</span>
                    </td>
                    <td className="p-4 pr-6 text-right space-x-2">
                      <button onClick={() => handleOpenEdit(u)} className="p-1 rounded bg-[#20294A] text-slate-300 hover:text-white"><Edit2 className="h-3.5 w-3.5" /></button>
                      <button onClick={() => handleDelete(u.id)} className="p-1 rounded bg-red-950/20 text-red-450 hover:text-red-400"><Trash2 className="h-3.5 w-3.5" /></button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* CRUD Edit / Add Modal Form */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-[#101529] border border-[#1F2942] rounded-3xl w-full max-w-md overflow-hidden shadow-2xl relative">
            <div className="p-5 border-b border-[#1F2942]/80 bg-[#151C36] flex justify-between items-center">
              <h3 className="font-extrabold text-sm text-white uppercase tracking-wider">{modalMode} {activeSubTab.slice(0, -1)}</h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-white font-bold">&times;</button>
            </div>

            <form onSubmit={handleSave} className="p-6 space-y-4">
              {errorMsg && (
                <div className="p-3 bg-red-950/20 border border-red-900/30 text-red-400 rounded-xl flex items-center gap-2 text-xs">
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  <span>{errorMsg}</span>
                </div>
              )}

              {/* Plant Form Fields */}
              {activeSubTab === 'PLANTS' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Plant Name</label>
                    <input type="text" required value={plantForm.name} onChange={(e) => setPlantForm({ ...plantForm, name: e.target.value })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Location</label>
                    <input type="text" value={plantForm.location} onChange={(e) => setPlantForm({ ...plantForm, location: e.target.value })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Timezone</label>
                    <input type="text" value={plantForm.timezone} onChange={(e) => setPlantForm({ ...plantForm, timezone: e.target.value })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Description</label>
                    <textarea value={plantForm.description} onChange={(e) => setPlantForm({ ...plantForm, description: e.target.value })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none h-20" />
                  </div>
                </div>
              )}

              {/* Department Form Fields */}
              {activeSubTab === 'DEPTS' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Parent Plant</label>
                    <select value={deptForm.plant_id} onChange={(e) => setDeptForm({ ...deptForm, plant_id: parseInt(e.target.value) })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none">
                      {plants.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Department Name</label>
                    <input type="text" required value={deptForm.name} onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Description</label>
                    <textarea value={deptForm.description} onChange={(e) => setDeptForm({ ...deptForm, description: e.target.value })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none h-20" />
                  </div>
                </div>
              )}

              {/* Machine Form Fields */}
              {activeSubTab === 'MACHINES' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Department</label>
                    <select value={machineForm.department_id} onChange={(e) => setMachineForm({ ...machineForm, department_id: parseInt(e.target.value) })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none">
                      {depts.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Machine Name</label>
                    <input type="text" required value={machineForm.name} onChange={(e) => setMachineForm({ ...machineForm, name: e.target.value })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Machine Type</label>
                    <input type="text" required value={machineForm.type} onChange={(e) => setMachineForm({ ...machineForm, type: e.target.value })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Rated Capacity (kW)</label>
                    <input type="number" required value={machineForm.rated_capacity} onChange={(e) => setMachineForm({ ...machineForm, rated_capacity: parseFloat(e.target.value) })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none" />
                  </div>
                </div>
              )}

              {/* Device Form Fields */}
              {activeSubTab === 'DEVICES' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Parent Machine</label>
                    <select value={deviceForm.machine_id} onChange={(e) => setDeviceForm({ ...deviceForm, machine_id: parseInt(e.target.value) })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none">
                      {machines.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Device Name</label>
                    <input type="text" required value={deviceForm.name} onChange={(e) => setDeviceForm({ ...deviceForm, name: e.target.value })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Register Modbus Address</label>
                    <input type="text" required value={deviceForm.register_address} onChange={(e) => setDeviceForm({ ...deviceForm, register_address: e.target.value })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none" />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Unit</label>
                      <input type="text" required value={deviceForm.unit} onChange={(e) => setDeviceForm({ ...deviceForm, unit: e.target.value })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none" />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Device Type</label>
                      <input type="text" required value={deviceForm.type} onChange={(e) => setDeviceForm({ ...deviceForm, type: e.target.value })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Serial Number</label>
                      <input type="text" value={deviceForm.serial_number} onChange={(e) => setDeviceForm({ ...deviceForm, serial_number: e.target.value })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none" />
                    </div>
                    <div>
                      <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Firmware Version</label>
                      <input type="text" value={deviceForm.firmware_version} onChange={(e) => setDeviceForm({ ...deviceForm, firmware_version: e.target.value })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none" />
                    </div>
                  </div>
                </div>
              )}

              {/* User Form Fields */}
              {activeSubTab === 'USERS' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Username</label>
                    <input type="text" required value={userForm.username} onChange={(e) => setUserForm({ ...userForm, username: e.target.value })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none" />
                  </div>
                  <div>
                    <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Email Address</label>
                    <input type="email" required value={userForm.email} onChange={(e) => setUserForm({ ...userForm, email: e.target.value })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none" />
                  </div>
                  {modalMode === 'ADD' && (
                    <div>
                      <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Password</label>
                      <input type="password" required={modalMode === 'ADD'} value={userForm.password} onChange={(e) => setUserForm({ ...userForm, password: e.target.value })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none" />
                    </div>
                  )}
                  <div>
                    <label className="block text-slate-400 mb-1 font-bold uppercase tracking-wider text-[9px]">Role level</label>
                    <select value={userForm.role_id} onChange={(e) => setUserForm({ ...userForm, role_id: parseInt(e.target.value) })} className="w-full bg-[#0D1227] border border-[#1F2942] rounded-xl p-3 text-slate-100 focus:outline-none">
                      <option value={1}>Admin</option>
                      <option value={2}>Plant Manager</option>
                      <option value={3}>Engineer</option>
                      <option value={4}>Operator</option>
                      <option value={5}>Viewer</option>
                    </select>
                  </div>
                </div>
              )}

              <button 
                type="submit"
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-extrabold py-3.5 rounded-xl uppercase tracking-wider transition-all mt-4"
              >
                Save Record
              </button>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
