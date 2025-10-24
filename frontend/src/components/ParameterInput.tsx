/**
 * ParameterInput - Single parameter input component for playbook execution
 * Reduces complexity of PlaybookExecutionDialog by extracting parameter rendering logic
 */

import {
  FormControl,
  FormLabel,
  Select,
  MenuItem,
  TextField,
  Typography,
} from '@mui/material';
import type { ParameterInfo, CredentialInfo } from '../types/api';

interface ParameterInputProps {
  parameter: ParameterInfo;
  value: string;
  credentials?: CredentialInfo[];
  onChange: (name: string, value: string) => void;
}

export function ParameterInput({
  parameter,
  value,
  credentials = [],
  onChange,
}: ParameterInputProps) {
  const handleChange = (newValue: string) => {
    onChange(parameter.name, newValue);
  };

  return (
    <FormControl fullWidth>
      <FormLabel htmlFor={`param-${parameter.name}`} sx={{ mb: 0.5, fontSize: '0.875rem' }}>
        {parameter.name}
        {parameter.required && ' *'}
      </FormLabel>

      {parameter.type === 'credential' ? (
        <Select
          id={`param-${parameter.name}`}
          value={value || ''}
          onChange={(e) => handleChange(e.target.value)}
          displayEmpty
          size="small"
          inputProps={{
            'aria-label': `${parameter.name} credential`,
          }}
        >
          <MenuItem value="" disabled>
            Select credential...
          </MenuItem>
          {credentials.map((cred) => (
            <MenuItem key={cred.name} value={cred.name}>
              {cred.name} ({cred.username})
            </MenuItem>
          ))}
        </Select>
      ) : parameter.type === 'file' ? (
        <TextField
          id={`param-${parameter.name}`}
          value={value || ''}
          onChange={(e) => handleChange(e.target.value)}
          placeholder="Enter file path..."
          size="small"
          fullWidth
          inputProps={{
            'aria-label': `${parameter.name} file path`,
          }}
        />
      ) : (
        <TextField
          id={`param-${parameter.name}`}
          value={value || ''}
          onChange={(e) => handleChange(e.target.value)}
          placeholder={parameter.default || `Enter ${parameter.name}...`}
          size="small"
          fullWidth
          inputProps={{
            'aria-label': parameter.name,
          }}
        />
      )}

      {parameter.description && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
          {parameter.description}
        </Typography>
      )}
    </FormControl>
  );
}
