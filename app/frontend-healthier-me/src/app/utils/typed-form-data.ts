import { ApiVoiceRequest } from "../types/api/requests/voice-request.type";

export class TypedFormData<T extends Record<string, any>> extends FormData {
    constructor(private form: T) {
        super();
        Object.keys(form).forEach(k => {
            if (form[k] instanceof Blob) {
                this.append(k, form[k]);
            } else {
                this.append(k, JSON.stringify(form[k]));
            }
        });
    }
}
