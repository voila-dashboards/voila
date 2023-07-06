import { BaseManager, User } from '@jupyterlab/services';
import { ReadonlyJSONObject } from '@lumino/coreutils';
import { ISignal, Signal } from '@lumino/signaling';

export class VoilaUserManager extends BaseManager implements User.IManager {
  userChanged: ISignal<this, User.IUser> = new Signal(this);
  connectionFailure: ISignal<this, Error> = new Signal(this);
  readonly identity: User.IIdentity | null = null;
  readonly permissions: ReadonlyJSONObject | null = null;

  refreshUser(): Promise<void> {
    return Promise.resolve();
  }

  get isReady(): boolean {
    return true;
  }

  get ready(): Promise<void> {
    return Promise.resolve();
  }
}
