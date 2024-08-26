/**
 * Convert BASE64 to BLOB
 */
export function convertBase64ToBlob(base64: string, contentType: string = "audio/*"): Blob {
    try {
        const byteCharacters = atob(base64); // Decode base64 string
        const byteArrays = [];

        for (let offset = 0; offset < byteCharacters.length; offset += 512) {
            const slice = byteCharacters.slice(offset, offset + 512);
            const byteNumbers = new Array(slice.length);
            for (let i = 0; i < slice.length; i++) {
                byteNumbers[i] = slice.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            byteArrays.push(byteArray);
        }

        return new Blob(byteArrays, { type: contentType });
    } catch (e) {
        console.error("Error decoding base64 string:", e);
        throw e;
    }
}
