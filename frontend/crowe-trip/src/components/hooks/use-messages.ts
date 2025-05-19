import { useEmployeeMessages } from './use-employee-messages';
import { useCompanyMessages } from './use-company-messages';
import { useMasterMessages } from './use-master-messages';

export const useMessages = (role: string) => {
  const employee = useEmployeeMessages();
  const company = useCompanyMessages();
  const master = useMasterMessages();

  if (role === 'EMPLEADO') return employee;
  if (role === 'EMPRESA') return company;
  if (role === 'MASTER') return master;

  throw new Error(`Rol no reconocido: ${role}`);
};
