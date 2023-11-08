import { Dialog as QuasarDialog } from 'quasar';

const confirm = (message: string, okCallback: () => void) => {
  QuasarDialog.create({
    message: message,
    cancel: true,
    persistent: true,
  }).onOk(okCallback);
};

export { confirm };
